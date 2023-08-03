import pyautogui
import time
import pyperclip3 as pc
import sys
import sqlite3
import urllib.parse as parse
import keyboard

print('waiting')
time.sleep(2)
textX, textY = pyautogui.position()
delX=0
delY=0
def getContent():
	global textX, textY
	pyautogui.click(textX, textY-300)
	pyautogui.hotkey('command', 'q')
	time.sleep(0.1)
	pyautogui.hotkey('command', 'c')
	return pc.paste()
def SendMessage(msg):
	global textX, textY
	pyautogui.click(textX, textY)
	pc.copy(msg)
	pyautogui.hotkey('command', 'v')
	pyautogui.press('enter')
def WaitForGenerating():
	last = getContent()
	while(True):
		new = getContent()
		pyautogui.scroll(-1000)
		time.sleep(1)
		if new == last:
			print("first check")
			print(new)
			if b'Regenerate' in new or b'Continue generating' in new:
				print("second check")
				if b'Stop generating' not in new:
					print("third check")
					break
		else:
			last = new
			print("waiting for gpt content generation")
con = sqlite3.connect("jobs.db")
cur = con.cursor()
#Delete errors in answers table and rescan corresponding jobs
res = cur.execute("SELECT * FROM answers WHERE answer IS 'ERROR'")
res = res.fetchall()
for i in res:
	cur.execute("DELETE FROM answers WHERE job="+str(i[2]))
	cur.execute("UPDATE jobs SET scanned=0 WHERE id="+str(i[2]))
con.commit()

nq =0
res = cur.execute("SELECT * FROM jobs WHERE scanned=0")
res = res.fetchall()
for i in res:
	#New ChatGPT conversation every 5 messages
	if nq % 5 == 0:
		if delX != 0 and delY != 0:
			pyautogui.click(delX, delY)
			time.sleep(1)
			pyautogui.press('enter')
			time.sleep(1)
		message = []
		message.append("For each job description, your task is to prepare an XML code containing answers to the questions the questions based on my resume and the job description.")
		#message.append("Never include more than one job in your answer and keep the questions order as provided.")
		message.append("Your XML answer should follow this template: <job-\{job_id\}><question-1>Answer to question 1</question-1><question-2>Answer to question 2</question-2></job-\{job_id\}> Replace \{job_id\} with the corresponding job offer unique identifier")
		#message.append("Job descriptions are independent. Forget each job description information after generating your XML response.")
		message.append("Only respond with the XML code and use the minimum number of words.")
		message.append("The questions:")
		bres = cur.execute("SELECT * FROM questions")
		bres = bres.fetchall()
		questions = []
		for item in bres:
			questions.append(item[0])
			message.append("Question " + str(len(questions)) + ": "+ item[1] +' (Accepted answer format:'+item[2]+')')
		message.append("My resume: "+ parse.unquote(sys.argv[1]))
		SendMessage('\n'.join(message))
		if delX == 0 and delY == 0:
			time.sleep(5)
			delX,delY = pyautogui.position()
		WaitForGenerating()
	if keyboard.is_pressed('esc'):
		break
	nq += 1
	message = []
	message.append('JOB OFFER UNIQUE IDENTIFIER: '+str(nq))
	message.append('JOB TITLE: '+i[2])
	message.append(i[5].replace('Show less', ''))
	SendMessage('\n'.join(message))
	WaitForGenerating()
	if '<job-'+str(nq)+'>' in str(pc.paste()):
		split = str(pc.paste()).split('<job-'+str(nq)+'>')
		if len(split) == 1:
			split = str(pc.paste()).split('<job-0'+str(nq)+'>')
			if len(split) > 1:
				split = split[len(split)-1].split('</job-0'+str(nq)+'>')[0]
			else:
				continue
		else:
			split = split[len(split)-1].split('</job-'+str(nq)+'>')[0]
		res = cur.execute("SELECT * FROM questions")
		res = res.fetchall()
		answers = []
		for i2 in range(len(questions)):
			answer = 'ERROR'
			while True:
				try:
					answer = split.split('<question-'+str(i2+1)+'>')[1].split('</question-'+str(i2+1)+'>')[0]
				except ZeroDivisionError as err:
					print(err)
				finally:
					break
			answers.append(answer)
		for i2 in range(len(answers)):
			cur.execute('INSERT INTO answers (question, answer, job) VALUES(?,?,?)', (questions[i2], answers[i2], i[0]))
			con.commit()
		cur.execute('UPDATE jobs SET scanned=? WHERE id=?', (round(time.time()), i[0]))
		con.commit()