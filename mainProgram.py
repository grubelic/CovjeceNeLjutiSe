from random import randint
from platform import python_version


PY_VERSION = (int(python_version().split('.')[0]),
              int(python_version().split('.')[1]),
              )
try:
    if(PY_VERSION[0] == 3 and (PY_VERSION[1] == 3 or PY_VERSION[1] == 4)):
        from importlib.machinery import SourceFileLoader
    else:
        from importlib import util
    importlibImported = True
except ImportError:
    importlibImported = False

importedModules = dict()

def convertPosition(position, color, relativeTo): #iz sustava color u relativeTo
    if(position < 1): return position
    return (position - 1 + (color - relativeTo + 4)*10)%40+1

def importModule(path):
    if(".py" in path and importlibImported):
        moduleName = path.split("/")[-1][:-3]
        if(moduleName in importedModules):
            return importedModules[moduleName]
        elif(PY_VERSION[1] < 5 and PY_VERSION[0] < 4):
            importedModules[moduleName] = SourceFileLoader(moduleName, path)
        else:
            spec = util.spec_from_file_location(moduleName, path)
            importedModules[moduleName] = util.module_from_spec(spec)
            spec.loader.exec_module(importedModules[moduleName])
    else:
        moduleName = path
        importedModules[moduleName] = __import__(moduleName)
    return importedModules[moduleName]

class Piece(object):
    def __init__(self, index, color, MIOCmod):
        self.MIOCmod = MIOCmod
        self.color = color
        self.index = index
        self.letter = "MIOC"[index]
        self.remove()
    def remove(self):
        self.position = 0
        self.absPosition = 0
    def move(self, dice):
        self.position = self.getNewPosition(dice)
        self.absPosition = convertPosition(self.position, self.color, 0)
    def getNewPosition(self, dice):
        if(self.position == 0):
            return 1
        elif(self.position > 0):
            np = self.position + dice
            return (np if np < 41 else 40 - np)
        else:
            return (self.position - dice)
    def canMove(self, dice):
        hl = self.index if self.MIOCmod else 3
        return (self.position == 0 and dice == 6 or \
                self.position > 0 and dice + self.position < 42 + hl or
                self.position < 0 and dice - self.position < 2 + hl)

class Player(object): #colorName i colorNumber
    def __init__(self, module, color, MIOCmod = True):
        self.isDisqualified = False
        self.main = module.main
        self.color = color
        self.pieces = []
        self.throwsRemaining = 3
        for i in range(4):
            self.pieces.append(Piece(i, color, MIOCmod))
    def canMove(self, piece, dice):
        if(piece.canMove(dice)):
            np = piece.getNewPosition(dice)
            for i in range(4):
                if(np == self.pieces[i].position):
                    return False
            return True
        return False
    def move(self, pieceIndex, dice):
        self.pieces[pieceIndex].move(dice)
        self.throwsRemaining = (0 if dice != 6 else 1)
    def allInYard(self):
        for i in range(4):
            if(self.pieces[i].position != 0):
                return False
        return True
    def allInHome(self):
        for i in range(4):
            if(self.pieces[i].position > -1):
                return False
        return True
    def remove(self, pieceIndex):
        self.pieces[pieceIndex].remove()
    def thrown(self):
        if(not(self.throwsRemaining)):
            self.throwsRemaining = (3 if self.allInYard() else 1)
        self.throwsRemaining -= 1
    def getAvailablePieces(self, dice):
        ap = []
        for piece in self.pieces:
            if(self.canMove(piece, dice)):
                ap.append(piece.letter)
        return "".join(ap)
    def reset(self, color):
        for piece in self.pieces:
            piece.remove()
            piece.color = color
        self.throwsRemaining = 3
        self.isDisqualified = False
        if(self.color != color):
            self.color = color
    def disqualify(self):
        self.isDisqualified = True
        for piece in self.pieces: piece.remove()

class Game(object):
    def throwDice(self, playerIndex):
        dice = randint(1, 6)
        if(self.eventHandler): 
            self.eventHandler("throwDice", (playerIndex, dice))
        return dice
    def getFirst(self):
        values = [0] * 4
        while True:
            for i in range(4):
                values[i] = randint(1, 6)
            if(self.eventHandler):
                self.eventHandler("getFirst", tuple(values))
            if(values.count(max(values)) == 1):
                return values.index(max(values))
    def move(self, playerIndex, pieceIndex, dice):
        self.players[playerIndex].move(pieceIndex, dice)
        absPos = self.players[playerIndex].pieces[pieceIndex].absPosition
        if(self.eventHandler): 
            self.eventHandler("move", (playerIndex, pieceIndex, absPos, dice))
        for i in range(4):
            if(i != playerIndex):
                for j in range(4):
                    if(absPos > 0 and self.players[i].pieces[j].absPosition == absPos):
                        self.players[i].remove(j)
                        if(self.eventHandler): 
                            self.eventHandler("remove", (playerIndex,
                                                         pieceIndex,
                                                         absPos, i, j))
                        return
    #players: objects of type core.Player, iterable of size 4
    #modules: iterable of size 4, str paths or imported bot modules, can be
    #         used instead of players argument, but is overriden by it
    #eventHandler: function which handles events when the game is displayed
    #MIOCmod: determines if pieces have to be sorted in their house at the end
    #returns index of player / bot who won the game
    def __init__(self,
                 players = None,
                 modules = None,
                 eventHandler = None,
                 MIOCmod = True):
        if(players):
            self.players = players
        else:
            #if modules are given as strings (path), create player arguments
            #using importModule, else assume they are given as module type
            self.players = []
            for index, module in enumerate(modules):
                if(type(module) is str):
                    module = importModule(module)
                self.players.append(Player(module, index, MIOCmod))
        self.eventHandler = eventHandler
    
    def start(self, playOrder = None):
        if(playOrder):
            self.players = [self.players[i] for i in playOrder]
        for i in range(4):
            self.players[i].reset(i)
        disqualifiedPlayers = 0
        currentPlayerIndex = self.getFirst()
        while True:
            currentPlayer = self.players[currentPlayerIndex]
            if(currentPlayer.isDisqualified):
                disqualifiedPlayers += 1
                #if three players are disqualified, the remaining one wins
                if(disqualifiedPlayers == 3):
                    for i in range(4):
                        if(not(self.players[i].isDisqualified)):
                            if(self.eventHandler):
                                self.eventHandler("gameOver", (i, ))
                            return i
                currentPlayerIndex = (currentPlayerIndex + 1) % 4
                continue
            else:
                disqualifiedPlayers = 0
            dice = self.throwDice(currentPlayerIndex)
            currentPlayer.thrown()
            ap = currentPlayer.getAvailablePieces(dice)
            if(ap):
                data = []
                for i in range(4):
                    data.append([])
                    for j in range(4):
                        data[i].append(self.players[i].pieces[j].absPosition)
                try:
                    pieceLetter = currentPlayer.main(data,
                                                     dice,
                                                     currentPlayerIndex,
                                                     ap)
                except Exception as e:
                    pieceLetter = type(e).__name__
                if(not(type(pieceLetter) is str
                       and len(pieceLetter) == 1
                       and pieceLetter in ap)):
                    print("\n\nColor:", currentPlayer.colorName,
                          "\nDice:", dice,
                          "\nPossible moves:", ap,
                          "\nYour output:", pieceLetter, sep = "")
                    print("\n\n Input:\n",
                          str((data, dice, currentPlayerIndex, ap)), sep = "")
                    if(self.eventHandler):
                        self.eventHandler("disqualify", (currentPlayerIndex,))
                    currentPlayer.disqualify()
                    currentPlayerIndex = (currentPlayerIndex + 1) % 4
                    continue
                self.move(currentPlayerIndex, "MIOC".index(pieceLetter), dice)
                if(currentPlayer.allInHome()):
                    if(self.eventHandler): 
                        self.eventHandler("gameOver", (currentPlayerIndex, ))
                    return currentPlayerIndex
            if(currentPlayer.throwsRemaining): continue
            currentPlayerIndex = (currentPlayerIndex + 1) % 4

if (__name__ == "__main__"):
    modules = []
    names = []
    for i in range(4 - len(modules)):
        names.append(input("Enter name of Bot" + str(i)+ ":\n"))
        if(names.count(names[-1]) > 1):
            modules.append(modules[names.index(names[-1])])
        else:
            modules.append(__import__(names[-1]))
    gm = Game(modules = modules)
    for i in range(int(input("Enter number of games: "))):
        print("Winner =", gm.start())
    input("Press enter to exit.")
        
