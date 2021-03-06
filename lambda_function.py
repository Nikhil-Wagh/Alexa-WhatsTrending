from pytrends.request import TrendReq
from bs4 import BeautifulSoup
import pandas as pd
import decimal
import datetime
from numpy import random


# python-lambda-local -f lambda_handler -t 10 lambda_function.py ./events/event.json

def lambda_handler(event, context):
	if event['request']['type'] == "LaunchRequest":
		return on_launch(event, context)
	elif event['request']['type'] == 'IntentRequest':
		return on_intent(event)
	elif event['request']['type'] == 'SessionEndedRequest':
		return on_session_ended()


# To get the value of slot  -- SLOT_NAME
# event['request']['intent']['slots']['SLOT_NAME']['value']
def on_launch(event, context):
	attributes = {
		'INDEX' : []
	}
	WelcomeMessages = [
		"Welcome to What's Trending!",
		"This is indeed trendy!",
		"Hello there, How may I help you?",
		"Welcome to the world of trends, What should I do for you today?",
		"Namaste, What can I do for you?",
		"Hello there, shall we get started?",
		"Welcome, What should I look for today?",
		"I'm so happy to see you.",
		"Hola, Without any further ado, let's get started.",
		"Bonjour, nice to meet you.",
		"Hello, let's find you some interesting topics.",
		"Welcome my lord, I grant you three tiny wishes. What are they?"
	]
	temp = getRandom(WelcomeMessages)
	return response_plain_text(temp, False, attributes, "Welcome", temp, "How can I help you?")


def on_intent(event):
	state = ""
	index = 0
	attributes = {
		'INDEX' : []
	}
	if 'attributes' in event['session']:
		attributes = event['session']['attributes']

	request = event['request']

	print(index, state)
	intent_name = request['intent']['name']
	print("\n\n %s \n\n" % intent_name )
	if intent_name == 'GetTrendingTopics' :
		return GetTrendingTopics(request, attributes)
	elif intent_name == 'GetTopCharts':
		return GetTopCharts(request)
	elif intent_name == 'GetRelatedTopics':
		return GetRelatedTopics(request)
	elif intent_name == 'GetSuggestionsIntent':
		return GetSuggestionsIntent(request)
	elif intent_name == "AMAZON.HelpIntent":
		return do_help()
	elif intent_name == "AMAZON.StopIntent":
		return do_stop(attributes)
	elif intent_name == "AMAZON.CancelIntent":
		return do_stop()
	else:
		print ("Invalid Intent reply with help")
		do_help()


def GetTrendingTopics(request, attributes):
	try:
		pytrend = TrendReq()
		trending_searches_df = pytrend.trending_searches(pn='p1')
	except Exception as e:
		print(type(e))
		print(e.args)
		ErrorMessages = [
			"Google is not very helpful sometimes, this is so embarrasing.",
			"Sorry for the inconvenience.",
			"This is so embarrasing that I can't help.",
			"Something wrong happened!",
			"There was an error fetching the details.",
			"There was a problem retrieving the data.",
			"Nobody is perfect, atleast I tried.",
			"Sorry for such an absurd behaviour. I can't help.",
			"There was an error",
			"Error's happen. That's what happened right now.",
			"An error occurred!",
			"Keep calm, light a fire and try again.",
			"The operation couldn't be completed."
		]
		temp = getRandom(ErrorMessages)
		return response_plain_text(temp, True, attributes, "Our apologies", temp)
	else:
		print("\nTotal number of topics ::", len(trending_searches_df))

		# outputSpeech = "Here are some trending topics ... "
		# cardContent = ""
		# extra = ""
		length = 3

		titles = []
		extra = ""
		for i in range(0, length + 1):
			title, articleTitle, article = getCurrentTopic(trending_searches_df, attributes)
			if articleTitle == "EMPTY":
				AllDoneMessages = [
					"Woooow, you have gone through all of our trending topics.",
					"Gone through all of them. Would you like to look for them again? Or you can always come later.",
					"I have this problem, I'm very sorry.",
					"I don't stop when I'm tired. I only stop when I'm done.",
					"Topics exhausted!",
					"I am all done.",
					"Do you want me to repeat.",
					"Nothing bad happened when I say I am done."
				]
				temp = getRandom(AllDoneMessages)
				return response_plain_text(
					temp,
					True,
					attributes,
					"I'm out of topics",
					temp,
					"I can tell you again, if you want."
				)
			elif i < length:
				titles.append(articleTitle)
			else:
				extra = title

		outputSpeech, cardContent = getOSandCC(titles, length, trending = True)
		TrueMessages = [
			"Here are some trending topics, ",
			"I've got something, ",
			"This is what I got, ",
			"Yes I've got something for you, ",
			"Maybe you will find this interesting, "
		]
		temp = getRandom(TrueMessages)
		"""
		return response_plain_text(
				temp + outputSpeech,
				False,
				attributes,
				"Trending Topics",
				cardContent,
				"Would you like to hear about " + extra + "?"
			)
		"""
		return response_ssml(
				temp + outputSpeech,
				True,
				attributes,
				"Trending Topics",
				cardContent,
				"Would you like to hear about " + extra + "?"
			)


def getCurrentTopic(trending_searches_df, attributes):
	index = getIndex(len(trending_searches_df), attributes)
	if index == -1:
		return ["EMPTY", "EMPTY", "EMPTY"] 
	current_topic = trending_searches_df.iloc[[index]]
	attributes = setIndex(index, attributes)

	title = current_topic['title'].values[0]
	articleTitle = BeautifulSoup(current_topic['newsArticlesList'].values[0][0]['title'], "lxml").text
	article = BeautifulSoup(current_topic['newsArticlesList'].values[0][0]['snippet'], "lxml").text

	if articleTitle[-1] == '.':
		articleTitle = articleTitle[:-1]

	return [title, articleTitle, article]


def getIndex(n, attributes):
	index_list = attributes['INDEX']
	if len(list(set(range(0, n - 1)) - set(index_list))) > 0:
		return random.choice(list(set(range(0, n - 1)) - set(index_list)))
	return -1


def setIndex(index, attributes):
	attributes['INDEX'].append(index)
	return attributes


def GetTopCharts(request, i = 0):
	pytrend = TrendReq()
	cid, keyword = getCid(request['intent'], 'WORD')
	print("\ncid ::", cid, "\nKeyword ::", keyword)

	# Validations
	if cid == -1:
		if keyword == -1:
			return keywordRequired()
		else:
			return getKeywordError(keyword)
	date = getDate(request['intent'], 'DATE')
	if date == -1:
		date = int(datetime.datetime.now().strftime ("%Y"))
		
		"""
	if cid == -1:
		FalseMessages = [
			"Please provide proper top charts topic.",
			"Sorry, I can't understand what you were looking for.",
			"I am not getting what you are looking for.",
			"Improper top charts topic!",
			"Don't have anything related to this."
		]
		temp = getRandom(FalseMessages)
		return response_plain_text(temp + " Would you like to hear about the topics which I support?",
		False,
		"Incorrect slot value",
		temp,
		"Would you like to hear about " + getRandomKeyword())
		"""

	try:
		date = date - i
		print("\ncid ::", cid, "\nDate ::", date)
		top_charts_df = pytrend.top_charts(cid = cid, date=date)
	except Exception as e:
		if i == 0:
			return GetTopCharts(request, i + 1)
		else:
			print(type(e))
			print(e.args)
			print("\ncid ::", cid, "\nDate ::", date)
			ApologyMessages = [
				"Sorry, I think I'm not feeling well today. I can't answer that.",
				"Sorry for the inconvenience.",
				"I am not getting what you are looking for.",
				"Something wrong happened!",
				"There was an error fetching the details.",
				"There was a problem retrieving the data.",
				"Nobody is perfect, atleast I tried.",
				"Sorry for such an absurd behaviour. I can't help.",
				"Don't have anything related to this."
			]
			temp = getRandom(ApologyMessages)
			return response_plain_text(temp, True, {}, "Our apologies", temp, "You can try again if you want.")
	else:
		length = 5
		titles = []
		for title in top_charts_df['title']:
			titles.append(title)

		outputSpeech, cardContent = getOSandCC(titles, length)
		TopChartsMessages = [
			"Here are some top ",
			"Here are the best  ",
			"This is what I've got related to ",
			"Yes I've got something for you regarding trending ",
			"Best in the category of "
		]
		temp = getRandom(TopChartsMessages)
		return response_plain_text(
				temp + keyword + " ... " + outputSpeech,
				True,
				{},
				"Top charts of " + keyword,
				cardContent,
				"Would you like to hear about " + getRandomKeyword()
			)
		

def getKeywordError(keyword):
	ErrorMessages = [
		"Sorry, information about " + keyword + " is not available.",
		"I am not getting anything for " + keyword,
		"Something wrong happened!, I can't find anything for " + keyword,
		"Cannot find anything for " + keyword + ".",
		"There was an error fetching the details about " + keyword,
		"There was a problem retrieving the data. I do not support the keyword " + keyword,
		"Nobody is perfect, atleast I tried. I'm sorry the keyword " + keyword + " is not supported yet",
		"Sorry for such an absurd behaviour. I can't find anything for " + keyword,
		"Don't have anything related to this."
	]
	temp = getRandom(ErrorMessages)
	return response_plain_text(
			temp,
			True,
			{},
			"Keyword error",
			"Cannot find the keyword you searched for.",
			"Would you like to hear about the topics which I support?"
		)


def getDate(intent, slot):
	slot = getSlotValue(intent, 'DATE')
	if type(slot) == str:
		slot = slot.split(' ')
		slot = ''.join(slot)
	return int(slot)


def GetSuggestionsIntent(request):
	keys = []
	while len(keys) < 5:
		temp = getRandomKeyword()
		if temp not in keys:
			keys.append(temp)

	outputSpeech, cardContent = getOSandCC(keys, len(keys))
	SuggestionMessages = [
		"Here are some suggestions ... ",
		"You can look for ... ",
		"Here's what I have for you. ",
		"I would recommend ",
		"Maybe you'll find this interesting. "
	]
	temp = getRandom(SuggestionMessages)
	return response_plain_text(
			temp + outputSpeech + " For example, you can say 'give me top charts of games'.",
			False,
			{},
			"Suggestions",
			outputSpeech,
			"What can I do for you?"
		)


def GetRelatedTopics(request):
	pytrend = TrendReq()
	keyword = getSlotValue(request['intent'], 'KEYWORD')

	if(keyword != -1):
		try:
			pytrend.build_payload(kw_list=[keyword])
			df = pytrend.related_topics()[keyword]
		except Exception as e:
			print(type(e))
			print(e.args)
			ErrorMessages = [
				"Google is not very helpful sometimes, this is so embarrasing.",
				"Sorry for the inconvenience.",
				"This is so embarrasing that I can't help.",
				"Something wrong happened!",
				"There was an error fetching the details.",
				"There was a problem retrieving the data.",
				"Nobody is perfect, atleast I tried.",
				"Sorry for such an absurd behaviour. I can't help.",
				"There was an error",
				"Error's happen. That's what happened right now.",
				"An error occurred!",
				"Keep calm, light a fire and try again.",
				"The operation couldn't be completed."
			]
			temp = getRandom(ErrorMessages)
			return response_plain_text(
					temp,
					True, 
					attributes,
					"Our apologies",
					"Sorry for the inconvenience",
					"What can I do for you?"
				)
		else:
			topics_df = df.sort_values(by='value', ascending=False)
			
			topics = []
			#random.shuffle(len(topics_df))
			for i, row in topics_df.iterrows():
				topics.append(row['title'])

			random.shuffle(topics)

			length = 5
			outputSpeech, cardContent, extra = getOSandCC(topics, length, True)
			AnswerMessages = [
				"Here are the topics related to ",
				"Here's what I have for you regarding ",
				"Here are some top topics related to ",
				"Here are the best topics related to ",
				"This is what I've got related to ",
				"Yes, I've got something for you regarding ",
				"Best topics in the category of "
			]
			temp = getRandom(AnswerMessages)
			return response_plain_text(
					temp + keyword + " ... " + outputSpeech,
					True,
					{},
					"Hot topics related to - " + keyword,
					cardContent,
					"Would you like to hear about " + extra
				)

	else:
		return keywordRequired()


def getOSandCC(lines, length, extraRequired = False, trending = False):
	outputSpeech = ""
	cardContent = ""
	extra = ""
	e = 1 if extraRequired else 0 # e = int(extraRequired)
	i = 0
	for line in lines:
		if i < length:
			outputSpeech += line.capitalize()
			cardContent += line.capitalize()
			if i < length - 2:
				outputSpeech += ", "
				if trending == True:
					outputSpeech += " <break time='0.3s'/> "
				cardContent += ",\n"
			elif i == length - 2:
				outputSpeech += ", and "
				if trending == True:
					outputSpeech += " <break time='0.3s'/> "
				cardContent += ", and\n"
			else: 
				outputSpeech += "."
				if extraRequired == False:
					break
		else:
			extra += line
			break
		i += 1

	if extraRequired :
		return outputSpeech, cardContent, extra
	else:
		return outputSpeech, cardContent


def keywordRequired():
	ReqMessages = [
		"The topic you searched for is not so clear.",
		"Sorry, the word you asked for is not available.",
		"I am not getting what you are looking for.",
		"Cannot find the keyword you searched for.",
		"Please tell me what to search for.",
		"I have a lot of data, please specify your keyword."
	]
	temp = getRandom(ReqMessages)
	return response_plain_text(
			temp,
			False,
			{},
			"Try these",
			"1. Try changing your sentences\n2. Try changing the search word(s).",
			"I can suggest you something if you want?"
		)


def getRandom(messages):
	return messages[random.randint(0, len(messages))] 


def response_plain_text(output, endsession, attributes, title, cardContent, repromt = ""):
	print(output + "\n")
	""" create a simple json plain text response  """
	return {
		'version'   : '1.0',
		'response'  : {
			'shouldEndSession'  : endsession,
			'outputSpeech'  : {
				'type'      : 'PlainText',
				'text'      : output
			},
			'card' : {
				'type' : 'Simple',
				'title' : title,
				'content' : cardContent    
			},
			'reprompt' : {
				'outputSpeech' : {
					'type' : 'PlainText',
					'text' : repromt
				}
			}
		},
		'sessionAttributes' : attributes
	}

def response_ssml(output, endsession, attributes, title, cardContent, repromt = ""):
	print(output + "\n")
	""" create a simple json plain text response  """
	return {
		'version'   : '1.0',
		'response'  : {
			'shouldEndSession'  : endsession,
			'outputSpeech'  : {
				'type'      : 'SSML',
				'ssml'      : '<speak> ' + output + '</speak>'
			},
			'card' : {
				'type' : 'Simple',
				'title' : title,
				'content' : cardContent    
			},
			'reprompt' : {
				'outputSpeech' : {
					'type' : 'PlainText',
					'text' : repromt
				}
			}
		},
		'sessionAttributes' : attributes
	}


def do_help():
	Messages = [
		"You can say 'what is trending', and I will tell you some of the viral topics.", 
		"You can say 'tell me who is in the top charts of actors', and I will tell you the top charts of actors. Or you can also change the list of top charts.", 
		"You can ask for 'topics related to some keyword' of your likes.",
		"You can ask for the 'topics which I support in the Top Charts', since they are limited."
	]
	return response_plain_text(
			getRandom(Messages) + " What can I do for you?",
			False,
			{},
			"My Features",
			"1. Trending Topics\n2. Top Charts\n3. Related Topics\n4. Suggestions to look for\n",
			"What can I do for you?"
		)

def do_stop(attributes):
	attributes['INDEX'] = {}
	Messages = [
		"Good Bye!!!",
		"Aloha",
		"Ciao",
		"Bon Voyage",
		"We'll meet again.",
		"Hope that I helped.",
		"Sayonara"
	]
	return response_plain_text(getRandom(Messages), True, {}, "Bye!", "I hope to see you again.") 
	
	

# event['request']['intent']['slots']['SLOT_NAME']['value']
def getSlotValue(intent, slot):
	if 'slots' in intent:
		if slot in intent['slots']:
			if 'value' in intent['slots'][slot]:
				return intent['slots'][slot]['value']

	return -1


def getCid(intent, keyword):
	slot = getSlotValue(intent, keyword)
	if slot != -1:
		slot = slot.lower()
		slot = slot.split(' ')
		slot = ''.join(slot)
		if slot == 'games' or slot == 'game':
			return 'games', 'games'
		elif slot == 'actor' or slot == 'actors':
			return 'actors', 'actors'
		elif slot == 'politicians' or slot == 'leaders':
			return 'politicians', slot
		elif slot == 'scientists':
			return 'scientists', slot
		elif slot == 'cars' or slot == 'sportscars':
			return 'sports_cars', slot
		elif slot == 'serials' or slot == 'seasons' or slot == 'realityshows':
			return 'reality_shows', slot
		elif slot == 'food' or slot == 'foods' :
			return 'foods', 'foods'
		elif slot == 'books' or slot == 'novels' or slot == 'comics':
			return 'books', slot
		elif slot == 'authors' or slot == 'writers':
			return 'authors', slot
		elif slot == 'songs' or slot == 'pop' or slot == 'music':
			return 'songs', slot
		elif slot == 'dogs' or slot == 'dogbreeds':
			return 'dog_breeds', slot
		elif slot == 'athletes':
			return 'athletes', slot
		elif slot == 'people' :
			return 'people', slot
		return -1, slot
	return -1, -1




def getRandomKeyword():
	Keywords = [
		'games',
		'actors',
		'politicians',
		'scientists',
		'sports cars',
		'reality shows',
		'foods',
		'books',
		'authors',
		'songs',
		'dog breeds',
		'athletes',
		'people'
	]
	return getRandom(Keywords)
