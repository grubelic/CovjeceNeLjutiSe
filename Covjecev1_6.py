import tkinter as tk
from tkinter import filedialog
import os
from threading import Thread
from time import sleep
from random import randint
from _tkinter import TclError
from sys import version_info
#dodati dozvoljene figure na kraj
#promijeniti layout yardova da budu 2x2

#konstante:
MAX_NUM = 5000
MY_NAME = "Covjecev1_6.py"
WINDOW_DIMS = 660, 660
NAMES = "MIOC"
COLORS = ["#FF0000", "#0000FF", "#00FF00", "#FFFF00"]
COLORS2 = ["#BB4444", "#4444BB", "#44BB44", "#BBBB22"]
COLOR_NAMES = ["red", "blue", "green", "yellow"]
COLORS = COLORS2 #Proba
CELL_BG = "#BBB986"
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
ALL_DISQUALIFIED = 8

class Window(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        global emptyImage, diceImages
        diceImages = [tk.PhotoImage(file = "dice/"+str(i+1)+".png") for i in range(6)]
        emptyImage = tk.PhotoImage()
        self.master.geometry("x".join((str(WINDOW_DIMS[0]), str(WINDOW_DIMS[1]))))
        self.master.resizable(False, False)
        self.place(x = 0, y = 0, width = WINDOW_DIMS[0], height = WINDOW_DIMS[1])
        self.sbView = SelectBotView(self)
        #self.menuView = MenuView(self)
class SelectBotView(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg = CELL_BG)
        self.quarters = []
        for i in range(4):
            self.quarters.append(Quarter(self, i))
        self.playButton = tk.Button(self, text = "PLAY", bg = "white", highlightthickness = 0, bd = 0)
        self.playButton.bind("<1>", self.play)
        self.playButton.place(x = WINDOW_DIMS[0]//2, y = WINDOW_DIMS[1]//2, anchor = tk.CENTER)
        self.place(x = 0, y = 0, width = WINDOW_DIMS[0], height = WINDOW_DIMS[1])
    def play(self, event):
        bots = []
        botNames = []
        for i in range(4):
            bots.append(self.quarters[i].returnValues["bot"])
            botNames.append(self.quarters[i].returnValues["botName"])
        if(None in bots):
            print("Select bots")
            return
        self.menuView = MenuView(self.master, bots, botNames)
        self.destroy()
class Quarter(tk.Frame):
    def __init__(self, master, color):
        tk.Frame.__init__(self, master, bg = COLORS[color], width = WINDOW_DIMS[0]//2, height = WINDOW_DIMS[1]//2)
        self.returnValues = dict(botName = "Player "+COLOR_NAMES[color]+" [HUMAN]", bot = None)
        self.color = color
        self.options = tuple([i[:-3] for i in os.listdir('.') if (i.endswith(".py") and i != MY_NAME)])
        if(self.options):
            self.selectOption(self.options[0])
        self.var = tk.StringVar()
        self.var.set(self.options[0])
        self.OM = tk.OptionMenu(self, self.var, *self.options, command = self.selectOption)
        self.OM.config(bg = COLORS[color], highlightthickness = 0, anchor = tk.W, width = 15)
        self.OM.pack(pady = (20, 20))
        if(version_info[0] == 3 and version_info[1] > 4):
            self.browseButton = tk.Button(self, bg =COLORS[color], text = "Browse", anchor = tk.W, command = self.browse, width = 17)
            self.browseButton.pack()
        self.place(x = color//2 * WINDOW_DIMS[1]//2, y = int(abs(-color + 1.5) - 0.5) * WINDOW_DIMS[0]//2, width = WINDOW_DIMS[0]//2, height = WINDOW_DIMS[1]//2)
    def browse(self):
        path = filedialog.askopenfilename(defaultextension = ".py", filetypes = [("Python Script", "*.py")])
        if(path):
            from importlib import util
            self.returnValues["botName"] = path.split("/")[-1][:-3]
            spec = util.spec_from_file_location(self.returnValues["botName"], path)
            self.returnValues["bot"] = util.module_from_spec(spec)
            spec.loader.exec_module(self.returnValues["bot"])
            self.var.set(self.returnValues["botName"])
    def selectOption(self, var):
        self.returnValues["botName"] = var
        self.returnValues["bot"] = __import__(var)
class MenuView(tk.Frame):
    def __init__(self, master, bots, botNames):
        tk.Frame.__init__(self, master, bg = CELL_BG)
        classes = [("Show Stats", TableStats), ("Display Board", TableDisplay)]
        buttons = []
        for i in range(2):
            buttons.append(tk.Button(self, text = classes[i][0]))
            buttons[i].pack()
            buttons[i].bind("<Button-1>", lambda x: GameView(self, classes[buttons.index(x.widget)][1], bots, botNames))
        self.place(x = 0, y = 0, width = WINDOW_DIMS[0], height = WINDOW_DIMS[1]) 
class GameView(tk.Frame):
    def __init__(self, master, tableClass, bots, botNames):
        tk.Frame.__init__(self, master, bg = CELL_BG)
        self.bind("<BackSpace>", lambda x: self.destroy())
        self.bots = bots
        self.botNames = botNames
        self.table = tableClass(self, self.botNames)
        self.players = [Player(i, self.botNames[i], self.bots[i]) for i in range(4)]
        self.gameThread = Thread(target = self.gameFunction)
        self.gameThread.start()
        self.focus_set()
        self.place(x = 0, y = 0, width = WINDOW_DIMS[0], height = WINDOW_DIMS[1])
    def gameFunction(self, numberOfGames = MAX_NUM):
        try:
            for i in range(numberOfGames):
                self.setTableUp()
                currentPlayerIndex = self.table.getFirst()
                disqualified = 0
                while True:
                    currentPlayerIndex %= 4
                    currentPlayer = self.players[currentPlayerIndex]
                    if (currentPlayer.disqualified):
                        disqualified += 1
                        if(disqualified == 4):
                            self.table.celebrate(ALL_DISQUALIFIED, self.players)
                            break
                    else:
                        disqualified = 0
                    dice = self.table.throwDice(currentPlayerIndex)
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
                        if not((type(pieceCoordinates) is list or type(pieceCoordinates) is tuple) and tuple(pieceCoordinates) in ap):
                            self.table.disqualify(currentPlayer)
                            print(ap, pieceCoordinates, "Bravo, cestitam!")
                            sleep(10)
                        self.table.movePiece(currentPlayer, pieceCoordinates, dice)
                        if currentPlayer.won:
                            self.table.celebrate(currentPlayerIndex, self.players)
                            break
                    if currentPlayer.getThrowsRemaining(): continue
                    currentPlayerIndex += 1
        except (RuntimeError, TclError):
            print("Over")
    def setTableUp(self):
        for player in self.players:
            for piece in player.pieces:
                self.table.toYard(piece)
        
class Table(object):
    def __init__(self, master):
        self.matrix = []
        for i in range(11):
            if not i or i == 10:
                self.matrix += [[" "]*4+["."]*3+[" "]*4]
            elif i < 4 or i < 10 and i > 6:
                self.matrix += [[" "]*4+["."]+["-"]+["."]+[" "]*4]
            elif i%2:
                self.matrix += [["."]+["-"]*4+[" "]+["-"]*4+["."]]
            else:
                self.matrix += [["."]*5+["-"]+["."]*5]
    def throwDice(self, color):
        return randint(1, 6)
    def getFirst(self):
        while True:
            values = [randint(1, 6) for i in range(4)]
            if(values.count(max(values)) == 1): return values.index(max(values))
    def addPiece(self, piece):
        self.matrix[piece.coordinates[0]][piece.coordinates[1]] = piece
    def removePiece(self, piece):
        self.matrix[piece.coordinates[0]][piece.coordinates[1]] = "."
    def disqualify(player):
        player.disqualified = True
        for piece in player.pieces:
            self.toYard(piece)
    def toYard(self, piece):
        self.removePiece(piece)
        piece.player.moveToYard(piece)
        self.addPiece(piece)
    def movePiece(self, p, pC, dice):
        piece = self.matrix[pC[0]][pC[1]]
        nC = piece.newCoordinates(dice)
        if(type(self.matrix[nC[0]][nC[1]]) is Piece):
            self.toYard(self.matrix[nC[0]][nC[1]])
        self.removePiece(piece)
        p.moveTo(piece, nC, dice)
        self.addPiece(piece)
        
class TableDisplay(Table):
    def __init__(self, master, names):
        Table.__init__(self, master)
        self.piecePic = []
        for i in range(4):
            self.piecePic.append([])
            for j in range(4):
                self.piecePic[i].append(tk.PhotoImage(file = "pieces/"+str(i)+str(j)+".png"))
        self.master = master
        self.display = []
        for i in range(11):
            self.display.append([])
            for j in range(11):
                self.display[i].append(tk.Label(master, 
             	                                image = emptyImage,
                                                relief = tk.SOLID,
                                                bd = self.matrix[i][j] == ".",
             	                                highlightthickness = 0,
                                                highlightbackground = "black",
                                                highlightcolor = "black",
             	                                bg = CELL_BG,
                                                width = 60-2*(self.matrix[i][j]=="."),
                                                height = 60-2*(self.matrix[i][j]==".")))
                self.display[i][j].grid(row = i, column = j)
        for i in range(4):
            self.display[START_FIELDS[i][0]][START_FIELDS[i][1]].config(bg = COLORS[i])
            for j in range(4):
                self.display[HOMES[i][j][0]][HOMES[i][j][1]].config(bg = COLORS[i])
    def celebrate(self, i, players):
        print(players[i].name, "won")
        return
    def addColor(self, c, exColor = None):
        if(not(exColor)):
            exColor = emptyImage
        returnValue = self.display[c[0]][c[1]].cget("image")
        self.display[c[0]][c[1]].config(image = exColor)
        return returnValue
    def addPiece(self, piece):
        super(TableDisplay, self).addPiece(piece)
        self.addColor(piece.coordinates, self.piecePic[piece.color][piece.number])
    def removePiece(self, piece):
        super(TableDisplay, self).removePiece(piece)
        self.addColor(piece.coordinates)
    def movePiece(self, p, pC, dice):
        piece = self.matrix[pC[0]][pC[1]]
        if(not pC in YARDS[p.color]):
            exColor = None
            for i in range(dice):
                self.addColor(piece.newCoordinates(i), exColor)
                nC = piece.newCoordinates(i + 1)
                exColor = self.addColor(nC, self.piecePic[piece.color][piece.number])
                sleep(.5)
        nC = piece.newCoordinates(dice)
        if(type(self.matrix[nC[0]][nC[1]]) is Piece):
            self.toYard(self.matrix[nC[0]][nC[1]])
        self.removePiece(piece)
        p.moveTo(piece, nC, dice)
        self.addPiece(piece)
        a = 0
        for i in self.matrix:
            for j in i:
                if(type(j) is Piece):
                    a += 1
        if(a > 16):
            print("Warning")
        sleep(.5)
    def throwDice(self, color):
        number = super(TableDisplay, self).throwDice(color)
        r = 2 + 6 * (color in (0, 3))
        s = 2 + 6 * (color // 2)
        self.display[r][s].config(image = diceImages[number-1])
        sleep(.5)
        self.display[r][s].config(image = emptyImage)
        sleep(.5)
        return number
    def getFirst(self):
        def resetLabels():
            for i in pictureLabels:
                i.config(bd = 0, image = emptyImage)
                i.grid(padx = 3, pady = 3)
        self.neWindow = tk.Toplevel(self.master, bg = CELL_BG)
        textLabels = [tk.Label(self.neWindow, text = self.master.players[i].name, width = 20, fg = COLORS2[i], bg = CELL_BG) for i in range(4)]
        pictureLabels = [tk.Label(self.neWindow,
                                  image = emptyImage,
                                  width = 60,
                                  height = 60,
                                  bg = "white",
                                  bd = 0,
                                  relief = tk.SOLID) for i in range(4)]
        for i in range(4):
            textLabels[i].grid(row =  int(abs(-i + 1.5) - 0.5), column = (i//2)*3)
            pictureLabels[i].grid(row = int(abs(-i + 1.5) - 0.5), column = (i//2)+1, padx = 3, pady = 3)
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

class TableStats(Table):
    cw = 500
    ch = 200
    def __init__(self, master, names):
        Table.__init__(self, master)
        self.master = master
        self.infoCanvas = tk.Canvas(master, width = TableStats.cw, height = TableStats.ch)
        self.numberOfGames = 0
        self.infoLabel = tk.Label(master, text = "Stats")
        self.infoLabel.place(x = WINDOW_DIMS[0]//2, y = 50, anchor = tk.N)
        self.lc = []
        for i in range(4): self.lc.append([(0, TableStats.ch),(1, TableStats.ch - 1)])
        self.infoCanvas.place(x = WINDOW_DIMS[0]//2, y = 50, anchor = tk.N)
        self.percentageL = [tk.Label(master, image = emptyImage, bg = COLORS[i]) for i in range(4)]
        self.lineIds = []
        self.progressBar = tk.Label(master, bg = "violet", image = emptyImage)
        self.progressBar.place(x = (WINDOW_DIMS[0]-TableStats.cw)//2, y = 55+TableStats.ch, anchor = tk.NW, width = 0, height = 20)
        self.nameLabels = [tk.Label(master, text = names[i], bg = COLORS[i])  for i in range(4)]
        for i in range(4):
            self.nameLabels[i].place(x = (WINDOW_DIMS[0]//5)*(i+1), y = WINDOW_DIMS[1] - 50, anchor = tk.S, width = 60)
            self.lineIds.append(self.infoCanvas.create_line(*tuple(self.lc[i]), fill = COLORS[i], width = 2))
            self.percentageL[i].place(x = (WINDOW_DIMS[0]//5)*(i+1), y = WINDOW_DIMS[1] - 50, anchor = tk.S, width = 60, height = 0)
    def upDate(self, players):
        self.progressBar.place(width = int(TableStats.cw*self.numberOfGames/MAX_NUM))
        for i in range(4):
            if(self.numberOfGames): self.percentageL[i].place(height = int(300*players[i].numberOfWins/self.numberOfGames))
            self.lc[i].append((self.lc[i][-1][0] + 1, int(TableStats.ch*(1-players[i].numberOfWins/MAX_NUM))))
            self.infoCanvas.delete(self.lineIds[i])
            self.lineIds[i] = self.infoCanvas.create_line(*tuple(self.lc[i]), fill = COLORS[i], width = 2)
        
    def celebrate(self, cpi, players):
        if(cpi != ALL_DISQUALIFIED):
            players[cpi].numberOfWins += 1
        if(not(self.numberOfGames%(MAX_NUM//500))):
            self.upDate(players)
        self.numberOfGames += 1
                
        

class Player(object):
    def __init__(self, color, name, module):
        self.numberOfWins = 0
        self.name = name
        self.disqualified = False
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
        piece.setCoordinates(YARDS[self.color][piece.number])
        if(self.allPiecesIn(YARDS[self.color])): self.throwsRemaining = 3
    def thrown(self):
        self.throwsRemaining -= 1
    def moveTo(self, piece, coordinates, dice):
        if(dice == 6): self.throwsRemaining = 1
        piece.setCoordinates(coordinates)
        self.won = self.allPiecesIn(HOMES[self.color])
    def getAvailablePieces(self, dice):
        def eatingOwnPiece(coordinates):
            for i in self.pieces:
                if i.coordinates == coordinates:
                    return True
            return False
        c = []
        for piece in self.pieces:
            if(dice == 6 and piece.coordinates in YARDS[self.color] and not(eatingOwnPiece(START_FIELDS[self.color]))):
                c.append(piece.coordinates)
            elif(not(piece.coordinates in YARDS[self.color]) and (self.path.index(piece.coordinates) + dice < len(self.path) - piece.number) and not(eatingOwnPiece(piece.newCoordinates(dice)))):
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
    def __str__(self):
        return str(self.color)
    def setCoordinates(self, coordinates):
        self.coordinates = coordinates
    def newCoordinates(self, dice):
        if(dice == 6 and self.coordinates in YARDS[self.color]):
            return(START_FIELDS[self.color])
        else:
            return(self.path[self.path.index(self.coordinates) + dice])


prozor = Window()
prozor.mainloop()
