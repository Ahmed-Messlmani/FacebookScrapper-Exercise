from fastapi import FastAPI
from requests_html import HTMLSession
import argparse
import time
import json
import csv
import re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup 
from requests_html import HTMLSession, HTML
from lxml.etree import ParserError
import sqlite3


def scroll_to_bottom(driver):
		x=0
		old_position = 0
		new_position = None

		while new_position != old_position and x<15:
			time.sleep(1)

			# Get old scroll position
			old_position = driver.execute_script(
					("return (window.pageYOffset !== undefined) ?"
					" window.pageYOffset : (document.documentElement ||"
					" document.body.parentNode || document.body);"))
			# Sleep and Scroll
			time.sleep(3)
			driver.execute_script((
					"var scrollingElement = (document.scrollingElement ||"
					" document.body);scrollingElement.scrollTop ="
					" scrollingElement.scrollHeight;"))
			# Get new position
			new_position = driver.execute_script(
					("return (window.pageYOffset !== undefined) ?"
					" window.pageYOffset : (document.documentElement ||"
					" document.body.parentNode || document.body);"))
			x+=1

class Scraper():

	def __init__(self,PageName):
		self.PageName = PageName
	def scrapedata(self):
		post_links=[]
		dates=[]
		times=[]
		likes=[]
		comments=[]
		texts=[]
		#driver = webdriver.Remote('http://selenium:8000/wd/hub',desired_capabilities=DesiredCapabilities.CHROME)
		driver = webdriver.Chrome(ChromeDriverManager().install())
		driver.get(f"https://m.facebook.com/{self.PageName}/")

		scroll_to_bottom(driver)

		page_source = driver.page_source

		#scraping html page data 
		soup = BeautifulSoup(page_source, 'lxml')
		section=soup.findAll('div',{'class':'_3drp'})
		for a in section[:100]:
			post_date_all=a.find('abbr')
			if post_date_all is None:
					times.append('nan')
			else:
				#for scraping date and time of post
				try:
					
					
					post_date=post_date_all.get_text(strip=True).split(',')
					
					date=post_date[0]
					time=post_date[1]
					dates.append(date)
					times.append(time)
				except:
					
					dates.append('today')
					times.append(post_date_all.get_text(strip=True) +' later')
					pass

			try:
				x=a.find('div',attrs={'class':'_52jc _5qc4 _78cz _24u0 _36xo'})
				post_link=x.find('a')['href']
				post_links.append("https://m.facebook.com/"+post_link)
				
			except:
				post_links.append('nan')

			try:
				#for scraping like of post
				like=a.find('span', attrs={'class':'like_def _28wy'})
				if(len(like) == 0):
					like ="0 likes"
				likes.append(like.get_text(strip=True).split(' ')[0]+' likes')
			except:
				likes.append("0 likes")
			
			#for scraping text of post
			try:

				text=a.find('div',{'class':'_5rgt _5nk5 _5msi'})
				post_text=text.find('p')
				if(len(post_text)==0):
					post_text =" "   
				texts.append(post_text.get_text(strip=True))
			except:
				texts.append('nan')
			try:

				#for scraping comment and share of post
				comment=a.find('span', attrs={'class':'cmt_def _28wy'})
				comments.append(comment.get_text(strip=True).split(' ')[0]+' comments')
				
			except:
				comments.append('0 comments')
				
				pass
		
		conn = sqlite3.connect('database.db')
		c = conn.cursor()
		#drop table if exist
		#c.execute("DROP TABLE page")
		#create a table
		c.execute('''CREATE TABLE page(text TEXT,post_linkes TEXT, likes TEXT, comments TEXT, dates TEXT ,times TEXT)''')

		qlist=[]
		
		for i in range(len(dates)):
			item={
					'text':texts[i],
					'post_linkes':post_links[i],
					'like': likes[i],
					
					'comments':comments[i],
					'date':dates[i],
					'times':times[i]
			}
			#insert and commit to database
			c.execute('''INSERT INTO page VALUES(?,?,?,?,?,?)''', (texts[i],post_links[i],likes[i],comments[i],dates[i],times[i]))
			conn.commit()
			print(item)
			qlist.append(item)
		#close database connection
		conn.close()
		return qlist
   
app=FastAPI()
quotes=Scraper("RealMadrid")
@app.get("/")
async def fread_item():
	return quotes.scrapedata()
