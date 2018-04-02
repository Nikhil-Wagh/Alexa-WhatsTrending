from pytrends.request import TrendReq
from bs4 import BeautifulSoup
import pandas as pd
import decimal
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
	return response_plain_text(getWelcomeMessage(), False, attributes, "Welcome", getWelcomeMessage(), "How can I help you?")

outputSpeech = "Hello"
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
	elif intent_name == "AMAZON.HelpIntent":
		return do_help()
	elif intent_name == "AMAZON.StopIntent":
		return do_stop()
	elif intent_name == "AMAZON.CancelIntent":
		return do_stop()
	else:
		print ("Invalid Intent reply with help")
		do_help()


def GetTrendingTopics(request, attributes):
	pytrend = TrendReq()
	trending_searches_df = pytrend.trending_searches()
	print("\nTotal number of topics ::", len(trending_searches_df))

	outputSpeech = "Here are some trending topics ... "
	cardContent = ""
	for i in range(0, 2):
		title, articleTitle, article = getCurrentTopic(trending_searches_df, attributes)
		if articleTitle == "EMPTY":
			return response_plain_text("Woooow, you have gone through all of our trending topics. Would you like to look for them again? Or you can always come later.",
			 False, attributes, "I'm out of topics", "I have this problem, I'm very sorry.",
			 "I can tell you again, if you want."
			)
		outputSpeech += (articleTitle + " ")
		cardContent += articleTitle + "\n" 


	return response_plain_text(outputSpeech, False, attributes, "Trending Topics", cardContent, "Would you like to hear more?")


def getCurrentTopic(trending_searches_df, attributes):
	index = getIndex(len(trending_searches_df), attributes)
	if index == -1:
		return ["EMPTY", "EMPTY", "EMPTY"] 
	current_topic = trending_searches_df.iloc[[index]]
	attributes = setIndex(index, attributes)

	printOnConsole(current_topic)

	title = current_topic['title'].values[0]
	articleTitle = BeautifulSoup(current_topic['newsArticlesList'].values[0][0]['title'], "lxml").text
	article = BeautifulSoup(current_topic['newsArticlesList'].values[0][0]['snippet'], "lxml").text

	if articleTitle[-1] != '.':
		articleTitle += '.'

	return [title, articleTitle, article]


def getIndex(n, attributes):
	index_list = attributes['INDEX']
	if len(list(set(range(0, n - 1)) - set(index_list))) > 0:
		return random.choice(list(set(range(0, n - 1)) - set(index_list)))
	return -1


def setIndex(index, attributes):
	attributes['INDEX'].append(index)
	return attributes


def GetTopCharts(request):
	pytrend = TrendReq()
	top_charts_df = pytrend.top_charts()

def GetRelatedTopics(request):
	pytrend = TrendReq()
	keyword = getSlotValue(request['intent'], 'KEYWORD')

	if(keyword != -1):
		pytrend.build_payload(kw_list=[keyword])
		df = pytrend.related_topics()[keyword]
		topics_df = df.sort_values(by='value', ascending=False)

		outputSpeech = "Here are the related topics corresponding to your search ... "
		cardContent = ""
		for index, row in topics_df.iterrows():
			outputSpeech += row['title'] + ", "
			cardContent += row['title'] + "\n"

		return response_plain_text(outputSpeech, True, {}, "Hot topics related to - " + keyword, cardContent, "Would you like to hear about .. ?")

	else:
		return keywordRequired()


def keywordRequired():
	return "Keyword is required for this function to work."

def printOnConsole(current_topic):
	print("Date :: ", u'{0}'.format(current_topic['date'].values[0]))
	print("Hotness Level :: %f" % decimal.Decimal(current_topic['hotnessLevel'].values[0]))
	print("Title :: %s" % current_topic['title'].values[0])
	print("Article Title :: %s" % BeautifulSoup(current_topic['newsArticlesList'].values[0][0]['title'], "lxml").text)
	print("Article :: %s" % BeautifulSoup(current_topic['newsArticlesList'].values[0][0]['snippet'], "lxml").text)
	print("Related Search list :: ", current_topic['relatedSearchesList'].values[0])
	print("\n")


def getRelatedSearchList(current_topic):
	current_topic['relatedSearchesList']


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

def getRandom(messages):
    return messages[random.randint(0, len(messages) - 1)] 

def response_plain_text(output, endsession, attributes, title, cardContent, repromt):
    print(output)
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
		"How can I help you?"
	]
	return getRandom(Messages)

def do_stop():
	global sessionAttributes
	attributes['INDEX'] = {}
	Messages = [
		'Good Bye!!'
	]
	return getRandom(Messages)
	

# event['request']['intent']['slots']['SLOT_NAME']['value']
def getSlotValue(intent, slot):
	if 'slots' in intent:
		if slot in intent['slots']:
			if 'value' in intent['slots'][slot]:
				return intent['slots'][slot]['value']

	return -1
