from pytrends.request import TrendReq
from bs4 import BeautifulSoup
import pandas as pd
import decimal
from numpy import random
import datetime

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
	return response_plain_text(getWelcomeMessage(), False, attributes, "Welcome", getWelcomeMessage(), "How can I help you?")


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
		return response_plain_text("Google is not very helpful sometimes, this is so embarrasing", True, attributes, "Our apologies", "Sorry for the inconvenience")
	else:
		print("\nTotal number of topics ::", len(trending_searches_df))

		# outputSpeech = "Here are some trending topics ... "
		# cardContent = ""
		# extra = ""
		length = 2

		titles = []
		extra = ""
		for i in range(0, length + 1):
			title, articleTitle, article = getCurrentTopic(trending_searches_df, attributes)
			if articleTitle == "EMPTY":
				return response_plain_text(
					"Woooow, you have gone through all of our trending topics. Would you like to look for them again? Or you can always come later.",
					True,
					attributes,
					"I'm out of topics",
					"I have this problem, I'm very sorry.",
				 	"I can tell you again, if you want."
				)
			elif i < length:
				titles.append(articleTitle)
			else:
				extra = title

		outputSpeech, cardContent = getOSandCC(titles, length)
		return response_plain_text(
				"Here are some trending topics, " + outputSpeech,
				False,
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
	keyword = getSlotValue(request['intent'], 'WORD')
	cid, keyword = getCid(request['intent'], 'WORD')

	# Validations
	if cid == -1:
		return getKeywordError()
	date = getDate(request['intent'], 'DATE')
	if date == -1:
		date = int(datetime.datetime.now().strftime ("%Y"))
	if cid == -1:
		return response_plain_text("Please provide proper top charts topic.",
		False,
		"Incorrect slot value",
		"Sorry, I can't understand what you were looking for.",
		"Would you like to hear about " + getRandomKeyword())

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
		    return response_plain_text("Sorry, I think I'm not feeling well today. I can't answer that", True, {}, "Our apologies", "Sorry, for the inconvenience", "You can try again if you want.")
	else:
		length = 5
		titles = []
		for title in top_charts_df['title']:
			titles.append(title)

		outputSpeech, cardContent = getOSandCC(titles, length)

		return response_plain_text(
				"Here are some top " + keyword + " ... " + outputSpeech,
				False,
				{},
				"Top charts of " + keyword,
				cardContent,
				"Would you like to hear about " + getRandomKeyword()
			)
   		

def getKeywordError():
	Messages = ["Sorry, the word you asked for is not available."]
	return response_plain_text(
			getRandomKeyword(Messages),
			False,
			{},
			"Keyword error",
			"Cannot find the keyword to search for.",
			"Would you like to hear the available topics?"
		)


def getDate(intent, slot):
	slot = getSlotValue(intent, 'DATE')
	if type(slot) == str:
		slot = slot.split(' ')
		slot = ''.join(slot)
	return int(slot)


def GetSuggestionsIntent(request):
	keys = []
	while len(keys) < 3:
		temp = getRandomKeyword()
		if temp not in keys:
			keys.append(temp)

	outputSpeech, cardContent = getOSandCC(keys, len(keys))

	return response_plain_text(
			"Here are some suggestions ... " + outputSpeech,
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
			return response_plain_text(
					"Google is not very helpful sometimes, this is so embarrasing",
					True, 
					attributes,
					"Our apologies",
					"Sorry for the inconvenience",
					"What can I do for you?"
				)
		else:
			topics_df = df.sort_values(by='value', ascending=False)
			
			topics = []
			for i, row in topics_df.iterrows():
				topics.append(row['title'])

			length = 5
			outputSpeech, cardContent, extra = getOSandCC(topics, length, True)

			return response_plain_text(
					"Here are the related topics related to " + keyword + " ... " + outputSpeech,
					False,
					{},
					"Hot topics related to - " + keyword,
					cardContent,
					"Would you like to hear about " + extra
				)

	else:
		return keywordRequired()


def getOSandCC(lines, length, extraRequired = False):
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
				cardContent += ",\n"
			elif i == length - 2:
				outputSpeech += " and "
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
	return response_plain_text(
			"The topic you searched for is not so clear.",
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


def do_help():
	Messages = [
		"You can say 'what is trending'.",
		"You can ask for some top charts.",
		"You can ask for related topics."
	]
	return response_plain_text(getRandom(Messages), True, {}, "Bye!", "I hope to see you again.")

def do_stop(attributes):
	attributes['INDEX'] = {}
	Messages = [
		'Good Bye!!'
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
		elif slot == 'songs' or slot == 'pop':
			return 'songs', slot
		elif slot == 'dogs' or slot == 'dogbreeds':
			return 'dog_breeds', slot
		elif slot == 'athletes':
			return 'athletes', slot
		elif slot == 'people' :
			return 'people', slot
		else :
			return -1, -1


def getWelcomeMessage():
	WelcomeMessages = [
	    "Welcome to Protone Dictionary!",
	    "This is Protone Dictionary!",
	    "Hello there, How may I help you?",
	    "Welcome to Protone Dictionary, What should I do for you today?",
	    "Welcome, What can I do for you?",
	    "Hello there, shall we get started?",
	    "Welcome, What should I look for today?",
	    "Welcome, did you find any new words?",
	    "Welcome, hope on to the world of words",
	    "I'm soo happy to see you."
	    "Hello, nice to meet you.",
	    "Hello, let's find meaning of some interesting words."
	]
	return getRandom(WelcomeMessages)


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

