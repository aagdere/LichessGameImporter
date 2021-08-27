import requests
from datetime import date
import pprint
import re
from time import sleep
import os

pp = pprint.PrettyPrinter(indent=4)
# This file must be in the current directory and populated with at least a single row
# 23306390957, GoZFrwHS
# The importer will import all games this month until it hits the one above
mappingFilename = "ChessdotcomToLichess.csv"
chessDotComBearer = os.environ['CHESSDOTCOMBEARER']
headers = {'Authorization': f'Bearer {chessDotComBearer}'}
chessDotComToLichessGameIds = {}

lichessImportGameEndpoint = "https://lichess.org/api/import"

def makeChessDotComGameEndpoint(user):
	today = date.today()
	monthWithLeadingZero = today.strftime('%m')
	return f"https://api.chess.com/pub/player/{user}/games/{today.year}/{monthWithLeadingZero}"

def getChessdotcom(endpoint):
	print(f"Making a GET request to endpoint: {endpoint}")
	response = requests.get(endpoint, headers=headers)
	print(f"Got response: {response.status_code}")
	return response

def printGameData(game):
	del game['pgn']
	pp.pprint(game)

def addNewMapping(chessDotComId, lichessId):
	chessDotComToLichessGameIds[chessDotComId] = lichessId
	with open(mappingFilename, 'a') as f:
		f.write(f"{chessDotComId}, {lichessId}\n")

def importGames(games):
	importedANewGame = False
	for game in games:
		chessDotComId = game['url'].split('/')[-1]
		if chessDotComId in chessDotComToLichessGameIds:
			print(f"Chess.com game Id already imported: {chessDotComId}")
			return importedANewGame
		pgn = game['pgn']
		print("Attempting to post following game into Lichess:")
		printGameData(game)
		response = requests.post(lichessImportGameEndpoint, {'pgn': pgn}, headers=headers)
		print("Response:")
		if response.status_code == 200:
			pp.pprint(response.json())
			print("Imported game, storing mapping in db..")
			lichessId = response.json()['id']
			addNewMapping(chessDotComId, lichessId)
			importedANewGame = True
		else:
			while "Too many requests" in response.text:
				print("Rate limited issue, will retry")
				sleep(10)
				response = requests.post(lichessImportGameEndpoint, {'pgn': pgn}, headers=headers)
			if response.status_code != 200:
				print(f"Failure while importing game: {response.text}")
				exit(1)
			else:
				importedANewGame = True
		sleep(10)
	return importedANewGame

def loadExistingMappingFromFile():
	with open(mappingFilename, 'r') as f:
		for line in f.readlines():
			chessDotComId, lichessId = re.sub(r"\s", "", line).split(',')
			chessDotComToLichessGameIds[chessDotComId] = lichessId

def pollForGames(user):
	chessDotComGamesEndpoint = makeChessDotComGameEndpoint(user)
	chessDotComGamesThisMonth = getChessdotcom(chessDotComGamesEndpoint).json()['games'][::-1]
	return importGames(chessDotComGamesThisMonth)

def main():
	user = os.environ['CHESSDOTCOMUSERNAME']
	loadExistingMappingFromFile()
	while True:
		importedANewGame = pollForGames(user)
		# Once a minute if a game has been imported otherwise 5 sec
		if importedANewGame:
			sleep(30)
		else: 
			sleep(5)

secondsUntilRestart = 30
while True:
	try:
		main()
	except OSError as osError:
		print(f"OSError: {osError}")
	except Exception as error:
		print(f"Exception: {error}")
	print(f"App failed, waiting {secondsUntilRestart} seconds till restart...")
	sleep(secondsUntilRestart)
	print("Restarting now...")