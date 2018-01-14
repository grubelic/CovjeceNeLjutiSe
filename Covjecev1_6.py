import tkinter as tk
import os
from threading import Thread
#from time import sleep
from random import randint
def sleep(x): return
#dodati dozvoljene figure na kraj
#promijeniti layout yardova da budu 2x2

#konstante:
MY_NAME = "Covjecev1_6.py"
WINDOW_DIMS = 660, 660
NAMES = "MIOC"
COLORS = ["#FF0000", "#0000FF", "#00FF00", "#FFFF00"]
COLORS2 = ["#BB4444", "#4444BB", "#44BB44", "#BBBB22"]
CELL_BG = "#BBBB77"
YARDS = (((9, 0), (9, 1), (9, 2), (9, 3)),
	 ((1, 0), (1, 1), (1, 2), (1, 3)),
         ((1, 7), (1, 8), (1, 9), (1, 10)),
         ((9, 7), (9, 8), (9, 9), (9, 10)))
HOMES = (((9, 5), (8, 5), (7, 5), (6, 5)),
	 ((5, 1), (5, 2), (5, 3), (5, 4)),
	 ((1, 5), (2, 5), (3, 5), (4, 5)),
	 ((5, 9), (5, 8), (5, 7), (5, 6)))
START_FIELDS = ((10, 4), (4, 0), (0, 6), (6, 10))
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))

class Window(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        global emptyImage, diceImages
        diceImages = [tk.PhotoImage(file = str(i+1)+".png") for i in range(6)]
        emptyImage = tk.PhotoImage()
        self.master.geometry("x".join((str(WINDOW_DIMS[0]), str(WINDOW_DIMS[1]))))
        self.pack(expand = tk.YES, fill = tk.BOTH)
        self.gameView = GameView(self)

class GameView(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self)
        self.table = TableDisplay(self)
        if(not(self.importBots())):
            self.master.destroy()
            return
        self.players = [Player(i, self.botNames[i], self.bots[i]) for i in range(4)]
        for i, player in enumerate(self.players):
            for j, piece in enumerate(player.pieces):
                self.table.setOnBoard(piece, YARDS[i][j])
        self.gameThread = Thread(target = self.gameFunction)
        self.gameThread.start()
        self.pack(expand = tk.YES, fill = tk.BOTH)
    def gameFunction(self, numberOfGames = 1):
        for i in range(numberOfGames):
            self.setTableUp()
            currentPlayerIndex = self.table.getFirst()
            while True:
                currentPlayerIndex %= 4
                currentPlayer = self.players[currentPlayerIndex]
                dice = self.table.throwDice()
                currentPlayer.thrown()
                ap = currentPlayer.getAvailablePieces(dice)
                if len(ap):
                    data = []
                    for i in range(4):
                        data.append([])
                        for j in range(4):
                            data[i].append([])
                            for k in range(2): data[i][j].append(self.players[i].pieces[j].coordinates[k])
                    pieceCoordinates = tuple(currentPlayer.main(data, dice, currentPlayerIndex, ap))
                    if not(pieceCoordinates in ap):
                        dice = 0
                        print(ap, pieceCoordinates, "Bravo, cestitam!")
                    self.table.move(currentPlayer, pieceCoordinates, dice)
                    if currentPlayer.won:
                        print(self.botNames[currentPlayerIndex], "won")
                        return
                if currentPlayer.getThrowsRemaining(): continue
                currentPlayerIndex += 1
    def setTableUp(self):
        for player in self.players:
            for piece in player.pieces:
                self.table.toYard(player, piece)
    def importBots(self):
        self.botNames = [i[:-3] for i in os.listdir('.') if (i.endswith(".py") and i != MY_NAME)]
        self.bots = [__import__(j) for i, j in enumerate(self.botNames) if i < 4]
        if(len(self.bots)):
            for i in range(4 - len(self.bots)):
                self.bots.append(self.bots[0])
                self.botNames.append(self.botNames[0])
            return 1
        else:
            print("Please add bots in this directory. (" + os.path.dirname(__file__) + ")")
            return 0
        
class Table(object):
    def __init__(self):
        self.matrix = [[0]*4 + [1]*3 + [0]*4 for i in range(4)]
        self.matrix += [[1]*11 for i in range(3)] + self.matrix[:]
        self.matrix[5][5] = 0
    def setOnBoard(self, piece, coordinates):
        piece.setCoordinates(coordinates)################
        self.matrix[coordinates[0]][coordinates[1]] = piece
    def throwDice(self):
        return randint(1, 6)
    def getFirst(self):
        while True:
            values = [randint(1, 6) for i in range(4)]
            if(values.count(max(values)) == 1): return values.index(max(values))
    def addpiece(self, piece):
        self.matrix[piece.coordinates[0]][piece.coordinates[1]] = piece
    def removepiece(self, piece):
        self.matrix[piece.coordinates[0]][piece.coordinates[1]] = 1
    def toyard(self, p, piece):
        self.removepiece(piece)
        p.moveToYard(piece)
        self.addpiece(piece)
    def move(self, player, oc, dice):
        piece = self.matrix[oc[0]][oc[1]]
        nc = piece.newCoordinates(dice)
        if(type(self.matrix[nc[0]][nc[1]]) is Piece):
            self.toyard(self.matrix[nc[0]][nc[1]].player, self.matrix[nc[0]][nc[1]])
        self.removepiece(piece)
        player.putPiece(piece, nc, dice)
        self.addpiece(piece)
       
class TableDisplay(Table):
    def __init__(self, master):
        Table.__init__(self)
        self.master = master
        self.display = []
        for i in range(11):
            self.display.append([])
            for j in range(11):
                self.display[i].append(tk.Label(master, 
             	                                image = emptyImage,
                                                relief = tk.SOLID,
                                                bd = self.matrix[i][j],
             	                                highlightthickness = 0,
                                                highlightbackground = "black",
                                                highlightcolor = "black",
             	                                bg = CELL_BG,
                                                width = 60-2*self.matrix[i][j],
                                                height = 60-2*self.matrix[i][j]))
                self.display[i][j].grid(row = i, column = j)
        for i in range(4):
            self.display[START_FIELDS[i][0]][START_FIELDS[i][1]].config(bg = COLORS[i])
            for j in range(4):
                self.display[HOMES[i][j][0]][HOMES[i][j][1]].config(bg = COLORS[i])
    def addPiece(self, piece):
        self.display[piece.coordinates[0]][piece.coordinates[1]].config(bg = piece.colorHex)
    def removePiece(self, piece):
        c = piece.coordinates
        bg = CELL_BG 
        for i in range(4):
            if c in HOMES[i] or c == START_FIELDS[i]:
                bg = COLORS[i]
        self.display[piece.coordinates[0]][piece.coordinates[1]].config(bg = bg)
    def throwDice(self):
        number = super(TableDisplay, self).throwDice()
        self.display[8][8].config(image = diceImages[number-1])
        sleep(1)
        return number
    def toYard(self, p, piece):
        self.removePiece(piece)
        super(TableDisplay, self).toyard(p, piece)
        self.addPiece(piece)
        sleep(.2)
    def move(self, player, oc, dice):
        nc = self.matrix[oc[0]][oc[1]].newCoordinates(dice)
        eaten = None
        if(type(self.matrix[nc[0]][nc[1]]) is Piece): eaten = self.matrix[nc[0]][nc[1]]
        self.removePiece(self.matrix[oc[0]][oc[1]])
        super(TableDisplay, self).move(player, oc, dice)
        self.addPiece(self.matrix[nc[0]][nc[1]])
        if eaten: self.addPiece(eaten)
        
                
    def getFirst(self):
        def resetLabels():
            for i in pictureLabels:
                i.config(bd = 0, image = emptyImage)
                i.grid(padx = 3, pady = 3)
        self.neWindow = tk.Toplevel(self.master)
        textLabels = [tk.Label(self.neWindow, text = self.master.players[i].name, width = 20) for i in range(4)]
        pictureLabels = [tk.Label(self.neWindow,
                                  image = emptyImage,
                                  width = 60,
                                  height = 60,
                                  bg = "white",
                                  bd = 0,
                                  relief = tk.SOLID) for i in range(4)]
        for i in range(4):
            textLabels[i].grid(row = i//2, column = (i%2)*2)
            pictureLabels[i].grid(row = i // 2, column = (i%2)*2+1, padx = 3, pady = 3)
        while True:
            sleep(1)
            values = []
            for i in range(4):
                values.append(randint(1, 6))
                pictureLabels[i].config(image = diceImages[values[i]-1])
                sleep(.5)
            for i in range(4):
                if (values[i] == max(values)):
                    pictureLabels[i].config(bd = 3)
                    pictureLabels[i].grid(padx = 0, pady = 0)
            sleep(2)
            if(values.count(max(values)) == 1):
                sleep(1)
                self.neWindow.destroy()
                return values.index(max(values))
            resetLabels()

class Player(object):
    def __init__(self, color, name, module):
        self.name = name
        self.won = False
        self.main = module.main
        self.colorHex = COLORS2[color]
        self.color = color
        self.pieces = []
        self.path = self.findMyPath()
        self.throwsRemaining = 3
        for i in range(4):
            self.pieces.append(Piece(color, i, self.path, self))
    def findMyPath(self):
        def nextTuple(previous, direction): return (previous[0]+direction[0], previous[1] + direction[1])
        l = [START_FIELDS[self.color]]
        direction = DIRECTIONS[self.color]
        while True:
            l.append(nextTuple(l[-1], direction))
            if(nextTuple(l[-1], direction) == (5, 5)): return l
            if(not(l[-1][0]%10 and l[-1][1]%10) and (4 in l[-1] or 6 in l[-1]) or (nextTuple(l[-1], direction) == l[0])):
               direction = DIRECTIONS[(DIRECTIONS.index(direction)+1)%4]
            elif(l[-1][0] == l[-1][1] or (4 in l[-1] and 6 in l[-1])):
               direction = DIRECTIONS[(DIRECTIONS.index(direction)+3)%4]
    def moveToYard(self, piece):
        self.won = False
        if(piece.coordinates in HOMES[self.color]): print("Warning!")
        piece.setCoordinates(YARDS[self.color][piece.number])
        if(self.allPiecesIn(YARDS[self.color])): throwsRemaining = 3
    def thrown(self):
        self.throwsRemaining -= 1
    def putPiece(self, piece, coordinates, dice):
        if(dice == 6): self.throwsRemaining = 1
        piece.setCoordinates(coordinates)
        self.won = self.allPiecesIn(HOMES[self.color])
    def getAvailablePieces(self, dice):
        def eatingMyself(self, index):
            for i in self.pieces:
                if i.coordinates == self.path[index]:
                    return True
                    print(True)
            return False
        c = []
        for piece in self.pieces:
            if(dice == 6 and piece.coordinates in YARDS[self.color]):
                c.append(piece.coordinates)
            elif(piece.coordinates in YARDS[self.color]):
                continue
            elif(self.path.index(piece.coordinates) + dice < len(self.path) - piece.number) and not(eatingMyself(self, self.path.index(piece.coordinates) + dice)):
                c.append(piece.coordinates)
        return c
    def allPiecesIn(self, iterable):
        for piece in self.pieces:
            if not(piece.coordinates) in iterable: return False
        return True
    def getThrowsRemaining(self):
        if (not(self.throwsRemaining)):
            self.throwsRemaining = 1
            if(self.allPiecesIn(YARDS[self.color])):
                self.throwsRemaining = 3
            return 0
        return self.throwsRemaining
      
class Piece(object):
    def __init__(self, color, pieceNumber, path, player):
        self.player = player
        self.colorHex = COLORS2[color]
        self.path = path
        self.name = NAMES[pieceNumber]
        self.color = color
        self.number = pieceNumber
        self.coordinates = YARDS[self.color][pieceNumber]
    def setCoordinates(self, coordinates):
        self.coordinates = coordinates
    def newCoordinates(self, dice):
        if(dice == 6 and self.coordinates in YARDS[self.color]):
            return(START_FIELDS[self.color])
        else:
            return(self.path[self.path.index(self.coordinates) + dice])


prozor = Window()
prozor.mainloop()
