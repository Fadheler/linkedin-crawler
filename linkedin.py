from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from time import strftime, localtime
import sqlite3
import re
import sys
import urllib.parse as parse

if __name__ == '__main__':
	con = sqlite3.connect("jobs.db")
	cur = con.cursor()
	driver = webdriver.Chrome()
	#driver.get('https://www.linkedin.com/jobs/search/?keywords=CFA&location=United%20States&geoId=103644278&f_TPR=r86400&f_E=2&position=1&pageNum=0')
	print(sys.argv)
	#time.sleep(int(sys.argv[1]))
	driver.get(parse.unquote(sys.argv[1]))
	driver.maximize_window()
	def get_content(xpath):
		element = driver.find_elements(By.XPATH, xpath)
		if len(element) > 0:
			return element[0].text
		else:
			return ""
	jobs = driver.find_elements(By.XPATH, '//ul[contains(@class, "jobs-search__results-list")]/li')
	print("Page loaded")
	if len(jobs) > 0:
		print("Jobs listed, will start scrolling...")
	else:
		print("No jobs found, exiting")
		exit()
	curheight = 0
	scroll = 0
	while(scroll < 20):
		height = driver.execute_script("return document.body.scrollHeight")
		if height > curheight:
			driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
			print("Scrolling down")
		elif len(driver.find_elements(By.XPATH, '//button[contains(@class, "infinite-scroller__show-more-button")]')) > 0:
			element = driver.find_elements(By.XPATH, '//button[contains(@class, "infinite-scroller__show-more-button")]')[0]
			if element.is_displayed() and element.is_enabled():
				print("Show more button clicked")
				element.click()
			else:
				print("Scrolling terminated")
				scroll = 20
		curheight = height
		time.sleep(1)
		scroll += 1
	print("Scrolling finished")
	#The final check for jobs after scrolling and clicking show more button.
	jobs = driver.find_elements(By.XPATH, '//ul[contains(@class, "jobs-search__results-list")]/li')
	print("Listed " + str(len(jobs)) + " jobs.")
	first = True
	for job in range(len(jobs)):
		if first == False:
			#Save the old offer content
			old_content = driver.find_elements(By.XPATH, "//div[contains(@class, 'details-pane__content')]")
			if len(old_content) > 0:
				old_content = old_content[0].get_attribute('innerHTML')
			else:
				old_content = ""
			driver.execute_script("window.scrollTo(0, "+ str(jobs[job].location["y"]) +");")
			#Click on the job offer
			jobs[job].click()
			#Check for the content to change (the new post to apper)
			retries = 0
			while(True):
				time.sleep(1)
				new_content = driver.find_elements(By.XPATH, "//div[contains(@class, 'details-pane__content')]")
				if len(new_content) > 0:
					if new_content[0].get_attribute('innerHTML') != old_content and len(get_content('//div[contains(@class, "top-card-layout__entity-info")]/a/h2')) > 2:
						retries = 0
						break
					else:
						retries += 1
					#Dirty fix: In case it takes too long (≈ 5seconds), it will go back to the previous offer and then try again with th new one
					if retries > 5:
						retries = 0
						driver.execute_script("window.scrollTo(0, "+ str(jobs[job-1].location["y"]) +");")
						jobs[job-1].click()
						time.sleep(1)
						jobs[job].click()

		else:
			#Directly get data from already displayed first job
			first = False

		#Job post loaded, fetch all details
		print("Fetching job #" + str(job+1))
		source = driver.find_elements(By.XPATH, '//div[contains(@class, "top-card-layout__entity-info")]/a')[0].get_attribute('href')
		source = source.split('?')[0]
		title = get_content('//div[contains(@class, "top-card-layout__entity-info")]/a/h2')
		employer = get_content('//div[contains(@class, "top-card-layout__entity-info")]/h4/div/span[1]/a')
		location = get_content('//div[contains(@class, "top-card-layout__entity-info")]/h4/div/span[2]')
		time_ago = get_content('//span[contains(@class, "posted-time-ago__text")]')
		#Approximate date of job offer publication
		time_approx = 0
		curtime = time.time()
		time_ago = time_ago.replace('ago', '')
		time_ago = time_ago.replace(' ', '')
		words = ['minute', 'hour', 'day', 'week', 'month', 'year']
		multipliers = [60, 60*60, 60*60*24, 60*60*24*7, 60*60*24*30, 60*60*24*7*365]
		for word in range(len(words)):
			if words[word] in time_ago:
				time_ago = time_ago.replace(words[word]+"s", '')
				time_ago = time_ago.replace(words[word], '')
				time_approx = time.time()-(int(time_ago)*multipliers[word])
				break
		link = driver.find_elements(By.XPATH, '//code[@id="applyUrl"]')
		if len(link) > 0:
			link = link[0].get_attribute('innerHTML')
			link = link.replace('<!--"', '')
			link = link.replace('"-->', '')
		else:
			link = driver.find_elements(By.XPATH, '//div[contains(@class, "top-card-layout__entity-info")]/a')[0].get_attribute('href')
		if len(driver.find_elements(By.XPATH, '//section[contains(@class, "show-more-less-html")]/button')) > 0:
			driver.find_elements(By.XPATH, '//section[contains(@class, "show-more-less-html")]/button')[0].click()
			time.sleep(0.25)
		description = get_content('//section[contains(@class, "show-more-less-html")]')
		recruiter = get_content('//div[contains(@class, "base-main-card__info")]/h3')
		recruiter_bio = get_content('//div[contains(@class, "base-main-card__info")]/h4')
		res = cur.execute("SELECT id FROM locations WHERE name=? OR keywords LIKE ?", (location, '%;'+location+';%')).fetchone()
		if res == None:
			cur.execute("INSERT INTO locations ('name') VALUES(?)", (location,))
			con.commit()
			location = cur.lastrowid
		else:
			location = res[0]
		res = cur.execute("SELECT id FROM employers WHERE name=? OR keywords LIKE ?", (employer, '%;'+employer+';%')).fetchone()
		if res == None:
			cur.execute("INSERT INTO employers ('name') VALUES(?)", (employer,))
			con.commit()
			employer = cur.lastrowid
		else:
			employer = res[0]
		res = cur.execute("SELECT id FROM jobs WHERE source=?", (source,)).fetchone()
		if res == None:
			cur.execute("INSERT INTO jobs ('source', 'title', 'employer', 'location', 'description', 'link', 'recruiter', 'published', 'created', 'scanned') VALUES (?,?,?,?,?,?,?,?,?,?);", (source, title, employer, location, description, link, recruiter, round(time_approx), round(time.time()), 0))
	driver.quit()
	print("Done")