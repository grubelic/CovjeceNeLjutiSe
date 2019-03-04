
import multiprocessing
import tkinter as tk
from time import sleep, time, strftime
from tkinter import font, filedialog
from _tkinter import TclError
from platform import python_version
from os import listdir, name
from random import shuffle
from threading import Thread
from math import log2
import mainProgram as core
import BotRandom

BOT_IDS = ('#005500', '#AAAA00', '#0000AA', '#AAFFFF',
           '#00FFFF', '#FF00AA', '#550055', '#55FF00',
           '#FFFFAA', '#555555', '#AA5500', '#FF5500',
           '#FF0000', '#272727', '#5555AA', '#00AA55',
           '#00AA00', '#FFAA55', '#AAAAFF', '#FFAA00',
           '#550000', '#AA0055', '#555500', '#0000FF',
           '#FF5555', '#AAAAAA', '#FFAAFF', '#AA0000',
           '#00AAFF', '#AA00FF', '#FFFF00', '#000000',
           )
BOARD_IDS = ("#00FF00", "#FFFF00", "#FF0000", "#0000FF")

#how players switch places when settings["pp"] is Balanced
SHUFFLE = ((0, 1, 2, 3), #0 1 2 3
           (0, 1, 3, 2), #0 1 3 2
           (0, 3, 1, 2), #0 2 1 3
           (0, 1, 3, 2), #0 2 3 1
           (0, 2, 3, 1), #0 3 1 2
           (0, 1, 3, 2), #0 3 2 1
           )

COLOURS = dict(bg = "#BABABA",
               ab = "#F3F5F7",
               fg = "#000000",
               ma = "#00797C",
               la = "#00B9C3",
               da = "#284141")

FONTS = dict(smaller = ("Arial Black", 10, "bold"),
             small = ("Arial Black", 16),
             medium = ("Arial Black", 20),
             large = ("Arial Black", 24),
             larger = ("Arial Black", 32))
NOT_BOTS = ("mainProgram_UI.py", "mainProgram.py")
PY_VERSION = tuple(map(int, python_version().split('.')))
ABH = 64 #Action Bar height
WW = 555*2
WH = WW//2 + ABH
W_DIMS = 'x'.join((str(WW), str(WH)))
SETTINGS_PP = ("UserDefined", "Balanced", "Random")

class ProgressBar(tk.Frame):
    def __init__(self, fillColor, *args, **kwargs):
        tk.Frame.__init__(self, bg = COLOURS["ab"], *args, **kwargs)
        self.filledPart = tk.Frame(self, bg = fillColor)
        emptyPart = tk.Frame(self, bg = COLOURS["ab"])
        emptyPart.grid(row = 0, column = 1, sticky = tk.NE + tk.SW)
        self.columnconfigure(0, weight = 0)
        self.columnconfigure(1, weight = 1)
        self.rowconfigure(0, weight = 1)
        self.gridded = False
    def updateFP(self, newValue, upperBound):
        self.columnconfigure(0, weight = newValue)
        self.columnconfigure(1, weight = upperBound - newValue)
        if(not(self.gridded) and newValue):
            self.filledPart.grid(row = 0, column = 0, sticky = tk.NE + tk.SW)
        elif(not(newValue)):
            #filledPart is not displayed at all when progress is at 0%
            self.filledPart.grid_forget()
        self.gridded = newValue != 0



#Buttons on ActionBar
class ActionButton(tk.Button):
    def __init__(self, side, *args, **kwargs):
        tk.Button.__init__(self,
                           *args,
                           **kwargs,
                           bg = COLOURS["la"],
                           highlightthickness = 0)
        self.pack(side = side, padx = (((ABH - 44) // 2) * (side == tk.LEFT),
                                       ((ABH - 44) // 2) * (side == tk.RIGHT),
                                       ))


#Base Class for all Frames that take up the whole window
#It has grid layout with actionBar filling first row. When inheriting,
#call cSpan method to declare number of columns in the grid.
class View(tk.Frame):
    def __init__(self, viewName, nextViewName, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.viewName = viewName
        self.actionBar = tk.Frame(self, bg = COLOURS["ma"], height = ABH)
        self.actionBar.grid(row = 0, column = 0, sticky = tk.NE + tk.SW)
        self.actionBar.pack_propagate(0)
        self.nextViewName = nextViewName[0]
        #list of tuples (stringsKey, widgetReference) to update after
        #changing language
        self.textViews = []
        if(not(viewName == "Main Menu")):
            self.backButton = ActionButton(side = tk.LEFT,
                                           master = self.actionBar,
                                           image = images["back"],
                                           command = self.back)
        else:
            self.master.title(strings["Ludo"])
            self.master.protocol("WM_DELETE_WINDOW", self.destroyView)
            if (name == "nt"):
                self.master.iconbitmap("res/drawables/icon.ico")
            self.master.geometry(W_DIMS)
        self.isDestroyed = False
        self.place(relwidth = 1, relheight = 1)

    #every View that uses multiple columns grid calls this
    def cSpan(self, columns):
        self.actionBar.grid_configure(columnspan = columns)

    def getNextView(self, intent = None):
        self.childView = getView(self.nextViewName, intent, self)

    def back(self):
        self.isDestroyed = True
        self.destroy()

    def updateTextViews(self):
        for i in self.textViews:
            i[1].config(text = strings[i[0]])

    #gives time to broadcastReceivers to stop updating screen
    #in the safest and the most elegant way
    def fadeOut(self, alpha = 1.0):
        alpha -= settings["fps"] / 25
        if(alpha > 0):
            self.master.attributes("-alpha", alpha)
            self.after(40, lambda: self.fadeOut(alpha))
        else:
            self.master.destroy()

    def destroyView(self):
        for view in filter(lambda w: (issubclass(type(w), View)),
                           self.winfo_children()):
            view.destroyView()
        if(type(self.master) is tk.Tk):
            self.after(40, self.fadeOut)
        else:
            self.isDestroyed = True

#Menus that lead to other Views
class MenuView(View):
    def __init__(self, viewName, nextViewName, intent, *args, **kwargs):
        View.__init__(self, viewName, nextViewName, *args, **kwargs)
        self.buttons = []
        self.columnconfigure(0, weight = 1)
        for i in range(len(nextViewName)):
            self.rowconfigure(i + 1, weight = 1)
            self.buttons.append(tk.Button(master = self,
                                          text = strings[nextViewName[i]],
                                          width = 10,
                                          bg = COLOURS["ma"],
                                          font = FONTS["medium"]))
            self.buttons[i].bind("<ButtonRelease-1>", self.setNextViewName)
            #for the sake of simplicity
            self.buttons[i].nextViewKey = nextViewName[i]
            self.buttons[i].grid(row = i + 1, column = 0)
            self.textViews.append((nextViewName[i], self.buttons[i]))

    def setNextViewName(self, event):
        self.nextViewName = event.widget.nextViewKey
        self.getNextView()


#Part of SelectBotsView, each instance displays info about one bot
class SelectBotFrame(tk.Frame):
    def __init__(self, botId, *args, **kwargs):
        tk.Frame.__init__(self, bg = botId, *args, **kwargs)
        #Stores bot's name, path and id, passed as tuple to next View
        self.module = ["BotRandom", "BotRandom", botId]
        #ne mijenjati opciju name jer ce onda svi sbFrameovi postati povezani
        #TODO: promijeniti inicijalizaciju i dodati podrsku za subfolder
        self.var = tk.StringVar(self, "BotRandom")
        #make letters visible on coloured background
        fgc = COLOURS["fg"] if isLight(botId) else COLOURS["ab"]
        self.options = [i[:-3] for i in listdir('.')
                        if (i.endswith(".py") and i not in NOT_BOTS)]
        self.OM = tk.OptionMenu(self,
                                self.var,
                                *self.options,
                                command = self.selectOption)
        self.OM.config(width = 12,
                       bg = botId,
                       fg = fgc,
                       highlightbackground = botId,
                       activebackground = botId,
                       activeforeground = fgc,
                       anchor = tk.CENTER)
        self.OM["menu"].config(bd = 0,
                               bg = COLOURS["ab"],
                               activebackground = botId,
                               activeforeground = fgc)
        self.OM.grid(row = 0, column = 0)
        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)
        #can't import modules using path on versions < 3.2
        if(PY_VERSION[0] > 3 or PY_VERSION[1] > 2 and PY_VERSION[0] == 3):
            self.browseButton = tk.Button(self,
                                          width = 15,
                                          text = strings["Browse"],
                                          command = self.browse,
                                          activebackground = botId,
                                          anchor = tk.CENTER,
                                          highlightthickness = 0,
                                          bg = botId,
                                          fg = fgc)
            self.browseButton.grid(row = 1, column = 0)
            self.rowconfigure(1, weight = 1)

    def selectOption(self, var):
        self.module[0] = var[:14]
        self.module[1] = var

    def browse(self):
        path = filedialog.askopenfilename(
            defaultextension = ".py",
            filetypes = [("Python Script", "*.py")])
        if(path):
            self.module[0] = path.split("/")[-1][:-3][:14]
            self.module[1] = path
            self.var.set(self.module[0])



#View in which user picks bots for match
class SelectBotsView(View):
    def __init__(self, viewName, nextViewName, intent, *args, **kwargs):
        View.__init__(self, viewName, nextViewName, *args, **kwargs)
        self.numberOfBots = tk.IntVar(
            self,
            16 if nextViewName[0] == "LeagueView" else 4,
            "Number of players")
        self.sbFrames = []
        self.playButton = ActionButton(side = tk.RIGHT,
                                       master = self.actionBar,
                                       image = images["play"],
                                       command = self.playCommand)
        if(self.nextViewName != "Board"):
            self.setingsButton = ActionButton(side = tk.RIGHT,
                                              master = self.actionBar,
                                              image = images["settings"],
                                              command = lambda: getView(
                                                    "Settings",
                                                    None,
                                                    self))
        if(nextViewName[0] == "TournamentView"):
            self.nobContainer = tk.Frame(self)
            for i in range(5, 1, -1):
                nobRadioButton = tk.Radiobutton(master = self.actionBar,
                                                variable = self.numberOfBots,
                                                value = 2**i,
                                                highlightthickness = 0,
                                                text = str(2**i),
                                                image = images["transparent"],
                                                height = 40, \
                                                compound = tk.CENTER,
                                                indicatoron = False,
                                                bg = COLOURS["la"],
                                                font = FONTS["large"],
                                                command = self.placeWidgets)
                nobRadioButton.pack(side = tk.RIGHT,
                                    padx = (0, 0 if (i != 5) else
                                               ((ABH - 44) // 2)))
            self.nobContainer.place(relx = 0.5,
                                    rely = 0.95,
                                    anchor = tk.CENTER)
        self.placeWidgets()

    #opens next View, gives it info about bots for import
    def playCommand(self):
        intent = [tuple(i.module) for i in self.sbFrames]
        if(settings["pp"] == "Random"):
            shuffle(intent)
        self.getNextView(intent)

    #populates grid with SelectBotsFrames
    def placeWidgets(self):
        nob = self.numberOfBots.get()
        self.cSpan(nob // 4)
        xnob = len(self.sbFrames)
        if(nob < xnob):
            for i in range(xnob - nob):
                if(i >= nob//4 and i < xnob // 4):
                    self.columnconfigure(i, weight = 0)
                self.sbFrames[-1].destroy()
                self.sbFrames.pop()
                self.textViews.pop()
        for frame in self.sbFrames:
            frame.grid_forget()
        if(nob > xnob):
            if(self.nextViewName == "Board" and settings["pp"] != "Random"):
                ids = BOARD_IDS
            else:
                ids = BOT_IDS[xnob:]
            for i in range(nob - xnob):
                self.sbFrames.append(SelectBotFrame(ids[i], self))
                self.textViews.append(("Browse",
                                       self.sbFrames[-1].browseButton))
        for i in range(4):
            self.rowconfigure(i + 1, weight = 3)
            for j in range(nob // 4):
                self.columnconfigure(j, weight = 1)
                self.sbFrames[i*nob//4 + j].grid(row = i + 1,
                                                 column = j,
                                                 padx = (0 if j else 8, 8),
                                                 pady = (0 if i else 8, 8),
                                                 sticky = tk.NE + tk.SW)


#Each BoardStat is part of BoardBotFrame and displays one of four stats
#in BoardView.
class BoardStat(tk.LabelFrame):
    def __init__(self, i, botId, *args, **kwargs):
        tk.LabelFrame.__init__(self, width = 528//4, *args, **kwargs)
        self.grid_propagate(0)
        self.valueLabel = tk.Label(self,
                                   text = "0",
                                   fg = botId,
                                   font = FONTS["larger"])
        self.columnconfigure(0, weight = 5)
        self.columnconfigure(1, weight = 1)
        self.rowconfigure(0, weight = 5)
        self.rowconfigure(1, weight = 1)
        self.valueLabel.grid(row = 0, column = 0, columnspan = 2)
        if(i < 2):
            self.progressBar = ProgressBar(botId, self)
            self.progressBar.grid(row = 1,
                                  column = 0,
                                  sticky = tk.NE + tk.SW,
                                  padx = (4, 0),
                                  pady = (0, 4))
            self.percentageLabel = tk.Label(self, text = "0%")
            self.percentageLabel.grid(row = 1, column = 1)
        else:
            self.unit = tk.Label(self, text = strings["Pcs"]
                                              if i == 2 else
                                              strings["Times"])
            self.unit.grid(row = 1, column = 0, columnspan = 2)
    def updateStat(self, newValue, upperBound = None):
        self.valueLabel.config(text = str(newValue))
        if(upperBound != None):
            self.progressBar.updateFP(newValue, upperBound)
            self.percentageLabel.config(
                text = str((newValue*100)//upperBound) + '%')


#One BoardBotFrame for every player in BoardView
class BoardBotFrame(tk.Frame):
    def __init__(self, botInfo, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs, bd = 1, relief = tk.RIDGE)
        self.grid_propagate(0)
        self.nameLabel = tk.Label(self,
                                  text = botInfo[0],
                                  fg = botInfo[2],
                                  font = FONTS["small"])
        self.nameLabel.grid(row = 0, column = 0, columnspan = 2)
        self.rowconfigure(0, weight = 1)
        for i in (0, 1):
            self.columnconfigure(i, weight = 1)
            self.rowconfigure(i + 1, weight = 4)
        self.labelFrames = []
        for i, text in enumerate(("Progress", "6s", "Ate", "Eaten")):
            self.labelFrames.append(BoardStat(i = i,
                                              botId = botInfo[2],
                                              master = self,
                                              text = strings[text]
                                              ))
            self.labelFrames[-1].grid(row = 1 + i // 2,
                                      column = i % 2,
                                      sticky = tk.NE + tk.SW)


#Stores "snapshots" of board changes that are displayed to viewer
#since the CHANGES are stored, not states, for each state there
#are two snapshots for each displaying direction (fwd or back)
class BoardStatesLog(object):
    def __init__(self):
        self.i = -1 #keeps track of state that is given by getLog
        self.step = 1 #1 for fwd, -1 for backwards
        #Here are changes stored while they're being made. When one
        #state is over, this is copied to log
        self.currentState = [[[dict()
                                for j in range(11)]
                                    for i in range(11)],
                             [[(0 , 1) if j < 2 else (0, None)
                                for j in range(4)]
                                    for i in range(4)]]
        #logs for storing copies of currentState for each state in game
        self.cellsLog = []
        self.bbfsLog = []
        self.expand()

    #used in BoardView.refreshScreen, returns log for next state
    def getLog(self):
        if(len(self.cellsLog) == 0): return (None, None)
        self.i += self.step
        if(self.i >= len(self.cellsLog)): self.i = len(self.cellsLog) - 1
        if(self.i < 0): self.i = 0
        #print(self.i)
        return (self.bbfsLog[self.i], self.cellsLog[self.i])

    #currently not used with custom rate, changes step of iteration over log
    def changeStep(self, rate = -1):
        self.i += self.step
        self.step *= rate

    def getStep(self):
        return self.step

    def setCurrent(self, r, c, kwargs):
        self.currentState[0][r][c].update(kwargs)

    def getCurrent(self, r, c, key):
        return self.currentState[0][r][c][key]

    def ucl(self, coords, kwargs): #update cellsLog
        r, c = coords
        for i in range(len(self.cellsLog[-1])):
            if(self.cellsLog[-1][i][0] == coords):
                self.cellsLog[-1][i][1].update(kwargs)
                break
        else: #if it's the first entry for given state and position
            #the 3rd part of the tuple is used for backwards iteration
            self.cellsLog[-1].append((coords,
                                      kwargs,
                                      self.currentState[0][r][c].copy()))
        self.currentState[0][r][c].update(kwargs)

    #similar to ucl, just for player stats displays
    def ubl(self, playerIndex, frameIndex, args):
        indices = playerIndex, frameIndex
        for i in range(len(self.bbfsLog[-1])):
            if(self.bbfsLog[-1][i][0] == indices):
                self.bbfsLog[-1][i][1] = args
                break
        else:
            self.bbfsLog[-1].append(
                (indices,
                 args,
                 self.currentState[1][playerIndex][frameIndex]))
        self.currentState[1][playerIndex][frameIndex] = args

    #marks the end of a state
    def expand(self):
        self.bbfsLog.append([])
        self.cellsLog.append([])


class BoardView(View):
    START_CELLS = ((0, 6), (6, 10), (10, 4), (4, 0))
    DICE_CELLS = ((2, 8), (8, 8), (8, 2), (2, 2))
    DIRECTIONS = ((1, 0), (0, -1), (-1, 0), (0, 1))
    YARDS = (((1, 7), (1, 8), (1, 9), (1, 10)),
             ((9, 7), (9, 8), (9, 9), (9, 10)),
             ((9, 0), (9, 1), (9, 2), (9, 3)),
             ((1, 0), (1, 1), (1, 2), (1, 3)))
    HOMES = (((1, 5), (2, 5), (3, 5), (4, 5)),
             ((5, 9), (5, 8), (5, 7), (5, 6)),
             ((9, 5), (8, 5), (7, 5), (6, 5)),
             ((5, 1), (5, 2), (5, 3), (5, 4)))
    def throwDice(self, args):
        playerIndex, dice = args
        coords = BoardView.DICE_CELLS[playerIndex]
        self.log.ucl(coords, {"image":images["dice/" + str(dice)]})
        self.players[playerIndex]["throws"] += 1
        self.players[playerIndex]["sixes"] += dice == 6
        self.log.ubl(playerIndex,
                     1,
                     (self.players[playerIndex]["sixes"],
                      self.players[playerIndex]["throws"]))
        self.log.expand()
        self.log.ucl(coords, {"image":images["transparent"]})
    def getFirst(self, args):
        values = args
        for playerIndex in range(4):
            self.players[playerIndex]["throws"] += 1
            self.players[playerIndex]["sixes"] += values[playerIndex] == 6
            self.log.ubl(playerIndex,
                         1,
                         (self.players[playerIndex]["sixes"],
                          self.players[playerIndex]["throws"]))
            #Highlight green all dice with maximum value
            for i, j in enumerate(BoardView.DICE_CELLS):
                if(i == playerIndex):
                    d = {"image":images["dice/" + str(values[i])]}
                else:
                    d = {}
                if (i <= playerIndex
                        and values[i] == max(values[:playerIndex + 1])):
                    d.update(bg = "green")
                else:
                    d.update(bg = COLOURS["bg"])
                self.log.ucl(j, d)
            self.log.expand()
        for i in BoardView.DICE_CELLS:
            self.log.ucl(i, dict(image = images["transparent"],
                                 bg = COLOURS["bg"]))
    def move(self, args):
        playerIndex, pieceIndex, pos, dice = args
        self.players[playerIndex]["pp"][pieceIndex] = \
            BoardView.getNewPos(self.players[playerIndex]["pp"][pieceIndex],
                                dice)
        progress = 0
        for i in range(4):
            if(i != pieceIndex):
                piecePos = self.players[playerIndex]["pp"][i]
                progress += piecePos if (piecePos > -1) else 40 - piecePos
        if(pos < 0):
            self.players[playerIndex]["pos"][pieceIndex] = \
                BoardView.HOMES[playerIndex][-(pos + 1)]
        else:
            self.players[playerIndex]["pos"][pieceIndex] = self.path[pos - 1]
        if(pos == core.convertPosition(1, playerIndex, 0)):
            self.log.ucl(BoardView.YARDS[playerIndex][pieceIndex],
                         dict(image = images["transparent"]))
            self.log.ucl(BoardView.START_CELLS[playerIndex],
                         dict(image = images["pieces/4" + str(pieceIndex)]))
            self.log.ubl(playerIndex, 0, (progress + 1, 170))
            return
        if(pos < 0):
            if(dice >= -pos):
                pos = core.convertPosition(40 - pos - dice, playerIndex, 0)
            else:
                pos += dice
        else:
            pos += 39 - dice
            pos %= 40
            pos += 1
        temp = images["transparent"]
        for i in range(dice):
            if(pos < 0):
                coords = BoardView.HOMES[playerIndex][-(pos + 1)]
            else:
                coords = self.path[pos - 1]
            self.log.ucl(coords, dict(image = temp))
            if(core.convertPosition(pos, 0, playerIndex) == 40):
                pos = -1
            else:
                pos += 1 + (pos < 0) * -2
            if(pos > 40): pos -= 40
            if(pos < 0):
                coords = BoardView.HOMES[playerIndex][-(pos + 1)]
            else:
                coords = self.path[pos - 1]
            temp = self.log.getCurrent(coords[0], coords[1], "image")
            if(coords in BoardView.HOMES[playerIndex]):
                pic = images["pieces/4" + str(pieceIndex)]
            else:
                pic = images["pieces/" + str(playerIndex) + str(pieceIndex)]
            self.log.ucl(coords, {"image":pic})
            piecePos = core.convertPosition(pos, 0, playerIndex)
            piecePos = piecePos if (piecePos > -1) else 40 - piecePos
            self.log.ubl(playerIndex, 0, (progress + piecePos, 170))
            #print(self.players[playerIndex])
            self.log.expand()

    #removes piece from board after it's eaten
    def remove(self, args):
        playerIndex = args[3]
        pieceIndex = args[4]
        self.players[playerIndex]["pp"][pieceIndex] = 0
        ateIndex = 5
        progress = 0
        for i in range(4):
            if(i != pieceIndex):
                piecePos = self.players[playerIndex]["pp"][i]
                progress += piecePos if (piecePos > -1) else 40 - piecePos
        self.log.ubl(playerIndex, 0, (progress, 170))
        for i in range(4):
            if (not(playerIndex == i) and
                    self.players[playerIndex]["pos"][pieceIndex] in
                    self.players[i]["pos"]):
                ateIndex = i
        if(ateIndex == 5): input(str(args))
        self.players[playerIndex]["eaten"] += 1
        self.players[ateIndex]["ate"] += 1
        self.log.ubl(playerIndex, 3, (self.players[playerIndex]["eaten"],))
        self.log.ubl(ateIndex, 2, (self.players[ateIndex]["ate"],))
        self.players[playerIndex]["pos"][pieceIndex] = \
                BoardView.YARDS[playerIndex][pieceIndex]
        self.log.ucl(BoardView.YARDS[playerIndex][pieceIndex],
                     dict(image = images["pieces/" +
                                  str(playerIndex) +
                                  str(pieceIndex)]))
    def disqualify(self, args):
        playerIndex = args[0]
        for i in range(4):
            self.log.ucl(self.players[playerIndex]["pos"][i],
                         dict(image = images["transparent"]))
            self.remove((None, playerIndex, i))
    def gameOver(self, arg):
        print("Game over:", arg[0])
    def pause(self):
        self.paused = not(self.paused)
        self.buttons["pause"].config(image = images["resume"
                                                    if self.paused else
                                                    "pause"])
    def changeSpeed(self, acc):
        self.fps += acc * 2
        if(self.fps == acc): self.log.changeStep()
        if(abs(self.fps) > 23):
            self.buttons["ff"
                         if self.fps > 0 else
                         "fb"].config(state = tk.DISABLED)
        self.buttons["ff" if acc < 0 else "fb"].config(state = tk.NORMAL)
    def findPath(color = 0):
        def nextTuple(previous, direction):
            return (previous[0] + direction[0], previous[1] + direction[1])
        DIRECTIONS = BoardView.DIRECTIONS
        L = [BoardView.START_CELLS[color]]
        direction = DIRECTIONS[color]
        while True:
            L.append(nextTuple(L[-1], direction))
            if(nextTuple(L[-1], direction) == L[0]): return L
            if(not(L[-1][0]%10 and L[-1][1]%10) and (4 in L[-1] or 6 in L[-1])):
               direction = DIRECTIONS[(DIRECTIONS.index(direction)+1)%4]
            elif(L[-1][0] == L[-1][1] or (4 in L[-1] and 6 in L[-1])):
               direction = DIRECTIONS[(DIRECTIONS.index(direction)+3)%4]
    def getNewPos(pp, dice): #previous position
        if(pp == 0):
            return 1
        elif(pp > 0):
            np = pp + dice
            return (np if np < 41 else 40 - np)
        else:
            return (pp - dice)
    EVENT_HANDLERS = {"throwDice" : throwDice, \
                      "getFirst" : getFirst, \
                      "move" : move, \
                      "disqualify" : disqualify, \
                      "remove" : remove, \
                      "gameOver" : gameOver}

    def gameThread(self, modules):
        game = core.Game(modules = modules,
                         eventHandler = self.eventHandler,
                         MIOCmod = settings["mod"] == "On")
        game.start()
    def eventHandler(self, action, data):
        try:
            BoardView.EVENT_HANDLERS[action](self, data)
        except (RuntimeError, TclError):
            pass
    def refreshScreen(self):
        while(True):
            while(self.paused):
                sleep(.1)
                if(self.isDestroyed): return
            if(self.isDestroyed): return
            bbfsLog, cellsLog = self.log.getLog()
            step = self.log.getStep()
            if(not(bbfsLog is None)):
                for l in bbfsLog:
                    i, j = l[0]
                    self.bbfs[i].labelFrames[j].updateStat(*l[step])
                for i in cellsLog:
                    r, c = i[0]
                    self.cells[r][c].config(**i[step])
            sleep(self.log.getStep() / self.fps)
    def __init__(self, viewName, nextViewName, intent, *args, **kwargs):
        View.__init__(self, viewName, nextViewName, *args, **kwargs)
        self.cSpan(3)
        self.fps = 1
        self.paused = False
        self.log = BoardStatesLog()
        self.path = BoardView.findPath()
        self.boardFrame = tk.Frame(self, width = WW//2, height = WW//2)
        self.bbfs = []
        for i in range(3):
            self.columnconfigure(i, weight = 1 + (i == 1))
            if(i): self.rowconfigure(i, weight = 1)
        for i in range(4):
            self.bbfs.append(BoardBotFrame(intent[i], self, width = 528//2))
            self.bbfs[i].grid(row = 1 + (i not in (0, 3)),
                              column = 2 * (i < 2),
                              sticky = tk.NE + tk.SW)
        self.boardFrame.grid(row = 1,
                             column = 1,
                             rowspan = 2,
                             sticky = tk.NE + tk.SW)
        self.cells = []
        for r in range(11):
            self.boardFrame.rowconfigure(r, weight = 1)
            self.boardFrame.columnconfigure(r, weight = 1)
            self.cells.append([])
            for c in range(11):
                self.log.setCurrent(r,
                                    c,
                                    {"bg":COLOURS["bg"],
                                     "image":images["transparent"]})
                self.cells[-1].append(tk.Label(self.boardFrame,
                                               bg = COLOURS["bg"],
                                               image = images["transparent"]))
                self.cells[-1][-1].grid(row = r, column = c, sticky = tk.NE + tk.SW)
        for r, c in self.path:
            self.log.setCurrent(r, c, {"bg":"white", "bd":1, "relief":"solid"})
            self.cells[r][c].config(bg = "white", bd = 1, relief = "solid")
        for i, j in enumerate(BoardView.START_CELLS):
            r, c = j
            self.log.setCurrent(r, c, {"bg":BOARD_IDS[i]})
            self.cells[r][c].config(bg = BOARD_IDS[i])
        for i in range(4):
            for j in range(4):
                r, c = BoardView.HOMES[i][j]
                self.log.setCurrent(r, c, {"bg":BOARD_IDS[i]})
                self.cells[r][c].config(bg = BOARD_IDS[i])
                r, c = BoardView.YARDS[i][j]
                self.log.setCurrent(r, c, {"image":images["pieces/" + str(i) + str(j)]})
                self.cells[r][c].config(image = images["pieces/" + str(i) + str(j)])
        self.buttons = {txt : ActionButton(side = tk.RIGHT,
                                           master = self.actionBar,
                                           image = images[txt],
                                           command = cmd)
                        for txt, cmd in zip(
                            ("ff", "pause", "fb"),
                            (lambda: self.changeSpeed(1), self.pause,
                             lambda: self.changeSpeed(-1)))}
        self.players = [dict(ate = 0, \
                             eaten = 0, \
                             sixes = 0, \
                             throws = 0, \
                             pos = list(BoardView.YARDS[i]), \
                             pp = [0, 0, 0, 0]) for i, j in enumerate(intent)]
        gThread = Thread(target = self.gameThread,
                         args = ([i[1] for i in intent],))
        gThread.start()
        notUIThread = Thread(target = self.refreshScreen)
        notUIThread.start()

class CustomLabel(tk.Label):
    def __init__(self, *args, **kwargs):
        tk.Label.__init__(self,
                         *args,
                         **kwargs,
                         font = FONTS["smaller"])
        self.config(text = kwargs["text"] + ':')

class CustomScale(tk.Scale):
    def __init__(self, name, *args, **kwargs):
        tk.Scale.__init__(self, *args, **kwargs)
        self.csName = name
        self.config(resolution = kwargs["to"] // 20 or 1,
                    length = 200,
                    orient = tk.HORIZONTAL)
    def getStr(self):
        return str(self.get())

class CustOptionMenu(tk.OptionMenu):
    def __init__(self, name, options, parent, *args, **kwargs):
        self.comVar = tk.StringVar()
        comOptions = [strings[option] for option in options]
        tk.OptionMenu.__init__(self, parent, self.comVar, *comOptions)
        self.name = name
        self["menu"].config(bd = 0,
                            bg = COLOURS["ab"],
                            activeforeground = COLOURS["ab"])
        self.getOption = dict()
        self.config(width = 12)
        for option in options:
            self.getOption[strings[option]] = option
    #needed when changing languages
    def updateOptions(self, newOptions):
        newVal = strings[self.get()]
        #thanks to iCodez from StackOverflow for this solution
        self.comVar.set(newVal)
        self["menu"].delete(0, 'end')
        for option in newOptions:
            self["menu"].add_command(label = strings[option],
                                     command = tk._setit(self.comVar,
                                                         strings[option]))
            self.getOption[strings[option]] = option

    def set(self, value):
        self.comVar.set(value)
    #overrides the function that returns translated version of option and
    #returns basic version of selected option e.g. "Croatian" -> "hr"
    def get(self):
        return self.getOption[self.comVar.get()]

    #gets str value of selected variable, like in CustomScale
    def getStr(self):
        return self.get()


class SettingsView(View):
    def __init__(self, viewName, nextViewName, intent, *args, **kwargs):
        View.__init__(self, viewName, nextViewName, *args, **kwargs)
        #we need new frame to use pack manager (perfect for this View)
        self.packFrame = tk.Frame(self)
        self.packFrame.grid(row = 1, column = 0)
        self.columnconfigure(0, weight = 1)
        self.svKeys = ("lang",
                       "pp",
                       "mod",
                       "gpm",
                       "fps",
                       *["ptsForPlace#" + str(i + 1) for i in range(4)])
        self.labels = []
        #options for a setting: if tuple contains string, setting is displayed
        #using tk.OptionMenu and that string has to be in strings dict.
        #if a tuple contains ints, those are from_ and to options of tk.Scale
        self.svValues = (("hr", "en"),
                         SETTINGS_PP,
                         ("On", "Off"),
                         (1, 10000),
                         (1, 25),
                         *[(0, 10) for i in range(4)])
        assert len(self.svKeys) == len(self.svValues)
        #setting widgets, one for each setting
        self.swidgets = dict()
        for key, options in zip(self.svKeys, self.svValues):
            #Scales from pfp cluster don't have labels above
            if(key[:-1] != "ptsForPlace#"):
                self.labels.append(CustomLabel(self.packFrame,
                                               text = strings[key]))
                self.textViews.append((key, self.labels[-1]))
                self.labels[-1].pack(pady = (8, 0))
            elif(key == "ptsForPlace#1"):
                self.labels.append(CustomLabel(self.packFrame,
                                               text = strings["pfp"]))
                self.textViews.append(("pfp", self.labels[-1]))
                self.labels[-1].pack(pady = (10, 0))
            if(type(options[0]) is str):
                self.swidgets[key] = CustOptionMenu(key,
                                                    options,
                                                    self.packFrame)
                self.swidgets[key].set(strings[settings[key]])
            else:
                self.swidgets[key] = CustomScale(key,
                                                 self.packFrame,
                                                 from_ = options[0],
                                                 to = options[1])
                self.swidgets[key].set(settings[key])
            self.swidgets[key].pack()
        self.saveImage = images["save"]
        self.saveButton =  ActionButton(side = tk.RIGHT,
                                        master = self.actionBar,
                                        image = self.saveImage,
                                        command = self.saveSettings)

    def updateTextViews(self):
        super(SettingsView, self).updateTextViews()
        for key, values in zip(self.svKeys, self.svValues):
            if(type(self.swidgets[key]) is CustOptionMenu):
                self.swidgets[key].updateOptions(values)
    def saveSettings(self):
        if(self.swidgets["lang"].get() != settings["lang"]):
            load("strings/" + self.swidgets["lang"].get())
            updateStrings(mainWindow)
        with open("res/settings.txt", 'w') as file:
            for key in self.svKeys:
                settings[key] = self.swidgets[key].get()
                file.write("|".join((key, self.swidgets[key].getStr())) + "\n")

class InfoView(View):
    def __init__(self, viewName, nextViewName, intent, *args, **kwargs):
        View.__init__(self, viewName, nextViewName, *args, **kwargs)
        self.columnconfigure(0, weight = 1)
        #self.rowconfigure(1, weight = 1)
        text = strings["infoView"].replace("PPP", "\n\n").replace("NNN", "\n")
        self.textBox = tk.Label(self,
                                text = text,
                                wraplength = WW // 10 * 7,
                                justify = tk.LEFT,
                                font = ("Arial", 16, "bold"))
        self.textBox.grid(row = 2, column = 0, pady = 32)
class TournamentView(View):
    ''' grid
    07 03 01 00 02 05 11
    08                12
    09 04          06 13
    10                14
    '''
    def __init__(self, viewName, nextViewName, intent, *args, **kwargs):
        View.__init__(self, viewName, nextViewName, *args, **kwargs)
        #Number of players
        lenin = len(intent)
        #Widgets containing match info, displayed in tree structure
        self.matchFrames = [None] * (lenin // 2 - 1)
        #refresh period in s
        self.rp = 1.0 / settings["fps"]
        div = 2
        #Number of columns and rows of grid
        columns = (int(log2(lenin)) - 1) * 2 - 1
        self.cSpan(columns)
        midCol = columns // 2
        rows = 1 + (lenin > 8) + 2 * (lenin > 16)
        #fills the list with actual MatchFrames, populating the
        #outermost MatchFrames with bot info
        while(div * 2 <= lenin):
            s = lenin // (div * 2) - 1
            e = lenin // div - 1
            for i in range(s, e):
                start = (i - s) * 4
                self.matchFrames[i] = MatchFrame(
                    players = [tuple(intent[j])
                               for j in range(start, start + 4)]
                              if div == 2 else \
                              [("N/A", None, COLOURS["la"])
                               for j in range(4)],
                    master = self)
            div *= 2
        for i in range(columns):
            self.columnconfigure(i, weight = 1)
        for i in range(rows):
            self.rowconfigure(i + 1, weight = 1)
        #the MatchFrame in the middle will always be displayed
        self.matchFrames[0].grid(row = 1,
                                 column = midCol,
                                 rowspan = lenin // 8 or 1)
        #gridding MatchFrames: first left side, then right
        if(lenin > 4):
            for i, l in zip((1, 2), ([], [])):
                s = 2 * i - 3 #side
                TournamentView.getPos(l, i, 2 - 16 // lenin)
                for j, r, c, rs in l:
                    self.matchFrames[j].grid(row = r + 1,
                                             column = s * (c + 1) + midCol,
                                             rowspan = rs)
        self.lastRefreshed = time()
        self.processes = []
        q = multiprocessing.Queue()
        #make the processing in separate processes to allow splitting
        #the work to multiple cores, leaving one spare
        self.availableCores = min((multiprocessing.cpu_count() - 1 or 1,
                                   lenin // 4))
        matchIDs = [[] for i in range(self.availableCores)]
        modules = [[] for i in range(self.availableCores)]
        cnt = lenin // 4 - 1
        #preparing arguments for processes
        while(cnt < lenin // 2 - 1):
            matchIDs[cnt % self.availableCores].append(cnt)
            modules[cnt % self.availableCores].append(
                [intent[(cnt + 1) * 4 - lenin + i][1] \
                 for i in range(4)])
            cnt += 1
        #to avoid string comparison in matchHandler
        ppToInt = SETTINGS_PP.index(settings["pp"])
        for i in range(self.availableCores):
            kw = [dict(modules = modules[i][j],
                       MIOCmod = settings["mod"] == "On") \
                  for j in range(len(modules[i]))]
            self.processes.append(multiprocessing.Process(
                target = matchHandler,
                args = (q,
                        matchIDs[i],
                        kw,
                        settings["gpm"],
                        ppToInt)))
        broadcastReceiverThread = Thread(target = self.receiveBroadcast,
                                         args = (q, ))
        broadcastReceiverThread.start()
        #IDs of matches that are played last in each process
        #after any of those is over, a new process can be created
        self.termIDs = []
        for i in range(len(self.processes)):
            self.termIDs.append(matchIDs[i][-1])
            self.processes[i].start()
        self.focus_set()
        self.bind("<Control-s>", self.export)

    def receiveBroadcast(self, q):
        gameNumbers = [0] * len(self.matchFrames)
        gpm = settings["gpm"]
        totalGames = gpm * len(gameNumbers)
        matchIDs = []
        modules = []
        finishedMatches = set()
        while(sum(gameNumbers) < totalGames and not(self.isDestroyed)):
            #if the game ended on refreshPeriod, display has to be updated
            if(time() - self.lastRefreshed > self.rp):
                for i in self.matchFrames:
                    i.updateDisplay()
                self.lastRefreshed = time()
            matchID, winner = q.get()
            self.matchFrames[matchID].newWin(winner)
            gameNumbers[matchID] += 1
            if(gameNumbers[matchID] == gpm and matchID):
                #check if 2 matches are over so a new match can be created
                #by taking top 2 players from bot sibling and matchID
                sibling = matchID - 1 + ((matchID & 1) << 1)
                if(sibling in finishedMatches):
                    matchIDs.append((matchID - 1) >> 1)
                    top4 = self.matchFrames[sibling].getTopPlayers() + \
                           self.matchFrames[matchID].getTopPlayers()
                    modules.append([top4[i][1] for i in range(4)])
                    self.matchFrames[matchIDs[-1]].setPlayers(top4)
                    finishedMatches.remove(sibling)
                else:
                    finishedMatches.add(matchID)
                for i in range(len(self.termIDs)):
                    #if it was the last match in whole process...
                    if(self.termIDs[i] == matchID):
                        #...wait for the process to terminate
                        self.processes[i].join()
                        self.processes[i].close()
                        if(modules):
                            #and create new one
                            kw = [dict(modules = modules[j],
                                       MIOCmod = settings["mod"] == "On") \
                                  for j in range(len(modules))]
                            self.processes[i] = multiprocessing.Process(
                                target = matchHandler,
                                args = (q,
                                        matchIDs,
                                        kw,
                                        settings["gpm"],
                                        SETTINGS_PP.index(settings["pp"])))
                            self.termIDs[i] = matchIDs[-1]
                            self.processes[i].start()
                            matchIDs.clear()
                            modules.clear()
        #often last game doesn't end on refreshPeriod, so last matchFrame
        #has to be updated at the end manually regardless of rp
        if(not(self.isDestroyed)):
            self.matchFrames[0].updateDisplay()
        for i in self.processes:
            try:
                if(i.is_alive()):
                    i.terminate()
            except ValueError:
                continue
    def export(self, event):
        filename = strftime("%c").replace(' ', '_').replace(':', '-') + ".txt"
        with open(filename, 'w') as file:
            for i in range(len(self.matchFrames)):
                mn = "Match #" + str(i) + "\n"
                file.write(mn)
                file.write(self.matchFrames[i].getData())
                file.write('\n\n')
    #fills list l with (index, row, abs(column - midColumn - 1), rowspan)
    #i.e. grid info about MatchFrame on index i
    def getPos(l, i, maxDepth, depth = 0, r = 0, isRight = 0):
        rs = 2 ** (maxDepth - depth)
        r += rs * isRight
        l.append((i, r, depth, rs))
        for j in range((maxDepth > depth) * 2):
            TournamentView.getPos(l,
                                  2 * (i + j) + (1 - j),
                                  maxDepth, depth + 1,
                                  r,
                                  j)

class MFPlayerInfo(object):
    def __init__(self, master, player, index):
        self.name, self.path, self.id = player
        self.labels = [tk.Label(master, bg = self.id),
                       tk.Label(master,
                                text = self.name,
                                width = 14),
                       tk.Label(master,
                                text = "0%",
                                width = 5)]
        self.index = index
        self.coords = []
        self.wins = 0
        self.rank = 0
    def updateLabel(self, NOGames):
        self.labels[2].config(text = "{:.2%}".format(self.wins / NOGames))
    def __ge__(self, other):
        return self.wins >= other.wins
    def __le__(self, other):
        return self.wins <= other.wins

#keeps track of match info and displays it
class MatchFrame(tk.Frame):
    MARGIN = (64, 32)
    GRAPH_DIMS = (600, 300)
    CANVAS_DIMS = (GRAPH_DIMS[0] + 2 * MARGIN[0],
                   GRAPH_DIMS[1] +  2 * MARGIN[1])
    def __init__(self, players, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs, bd = 1, relief = tk.RIDGE)
        #storing player info
        self.mfpi = [None for i in range(len(players))]
        self.toplevelDisplayed = False
        self.NOGames = 0
        #keeps track of original indices after sorting players
        self.order = [0, 1, 2, 3]
        #creating and displaying mfpi
        self.setPlayers(players)
        self.rowconfigure(4, weight = 1)
        self.columnconfigure(0, weight = 1)
        self.columnconfigure(1, weight = 8)
        self.columnconfigure(2, weight = 1)
        self.progressBar = ProgressBar(COLOURS["ma"], self)
        self.progressBar.grid(row = 4,
                              column = 0,
                              columnspan = 3,
                              sticky = tk.NE + tk.SW)
        #to avoid refreshing the display if nothing changed
        self.displayUpdated = True
        self.bind("<Button-1>", self.showTopLevel)
    def showTopLevel(self, event):
        self.toplevel = tk.Toplevel(self)
        self.toplevel.resizable(False, False)
        self.toplevel.protocol("WM_DELETE_WINDOW", self.hideTopLevel)
        self.canvas = tk.Canvas(self.toplevel,
                                width = self.CANVAS_DIMS[0],
                                height = self.CANVAS_DIMS[1],
                                bg = "#FFFFFF")
        axes = self.canvas.create_line(self.MARGIN[0],
                                       self.MARGIN[1],
                                       self.MARGIN[0],
                                       self.MARGIN[1] + self.GRAPH_DIMS[1],
                                       self.CANVAS_DIMS[0] - self.MARGIN[0],
                                       self.MARGIN[1] + self.GRAPH_DIMS[1],
                                       width = 2,
                                       arrow = tk.BOTH,
                                       arrowshape = (4, 5, 3))
        gpm = settings["gpm"]
        #calculating gridlines' positions (milestones)
        steps = ((50, 25), (25, 10), (10, 5))
        for i in range(2, -1, -1):
            for j in steps:
                if(gpm > j[0] * 10 ** i):
                    step = j[1] * 10 ** i
                    break
            else:
                continue
            break
        else:
            step = gpm // 3
        for i in range(0, gpm, step):
            #gridlines
            if(i): self.canvas.create_line(MatchFrame.gtc(0, i),
                                           MatchFrame.gtc(gpm, i),
                                           fill = "#BABABA",
                                           dash = (4, 2))
            #milestone marks on Y axis
            self.canvas.create_line((self.MARGIN[0] - 4,
                                     MatchFrame.gtc(None, i)),
                                    MatchFrame.gtc(0, i))
            #milestone marks on X axis
            self.canvas.create_line(MatchFrame.gtc(i, 0),
                                    (MatchFrame.gtc(i),
                                     self.GRAPH_DIMS[1] + self.MARGIN[1] + 4))
            #milestone labels on Y axis
            self.canvas.create_text(self.MARGIN[0]//2,
                                    MatchFrame.gtc(None, i),
                                    text = str(i),
                                    fill = "#BABABA")
            #milestone labels on X axis
            self.canvas.create_text(MatchFrame.gtc(i),
                                    self.GRAPH_DIMS[1] + self.MARGIN[1] * 1.5,
                                    text = str(i),
                                    fill = "#BABABA")
        self.trendlines = [[self.canvas.create_line(
                                *self.mfpi[i].coords,
                                fill = self.mfpi[i].id,
                                width = 2),
                            self.canvas.create_line(
                                *MatchFrame.gtc(0, self.mfpi[i].wins),
                                self.mfpi[i].coords[-2],
                                self.mfpi[i].coords[-1],
                                fill = self.mfpi[i].id,
                                dash = (4, 2)),
                            self.canvas.create_text(
                                self.MARGIN[0] // 2,
                                MatchFrame.gtc(None, self.mfpi[i].wins),
                                fill = self.mfpi[i].id,
                                text = str(self.mfpi[i].wins))]
                            for i in range(4)]
        self.canvas.pack()
        self.toplevelDisplayed = True
    def setPlayers(self, players):
        x1, y1 = MatchFrame.gtc(0, 0)
        for i in range(len(players)):
            if(self.mfpi[i]):
                for label in self.mfpi[i].labels:
                    label.destroy()
            self.mfpi[i] = MFPlayerInfo(self, players[i], i)
            #adding the two points needed to create a line on canvas
            for j in (x1 - 1, y1, x1, y1):
                self.mfpi[i].coords.append(j)
            self.rowconfigure(i, weight = 3)
            for j, k in enumerate(self.mfpi[i].labels):
                k.bind("<Button-1>", self.showTopLevel)
                k.grid(row = i, column = j, sticky = tk.NE + tk.SW)
            if(self.toplevelDisplayed):
                for j in range(3):
                    self.canvas.itemconfig(self.trendlines[i][j],
                                           fill = players[0])
                    self.canvas.itemconfig(self.trendlines[i][2],
                                           text = players[i][1])

    #converts game number to canvas coordinates
    def gtc(gameNumber = None, winNumber = None):
        if(gameNumber != None):
            x = MatchFrame.MARGIN[0] + \
                MatchFrame.GRAPH_DIMS[0] * gameNumber // settings["gpm"]
            if(winNumber == None): return x
        if(winNumber != None):
            y = MatchFrame.MARGIN[1] + \
                MatchFrame.GRAPH_DIMS[1] - \
                MatchFrame.GRAPH_DIMS[1] * winNumber // settings["gpm"]
            if(gameNumber == None): return y
        return (x, y)
    #fade added to make sure Toplevel won't be updated after it's destroyed
    def hideTopLevel(self, alpha = 1.0):
        self.toplevelDisplayed = False
        alpha -= 1 / 10
        if(alpha > 0):
            self.toplevel.attributes("-alpha", alpha)
            self.after(16, lambda: self.hideTopLevel(alpha))
        else:
            self.toplevel.destroy()
    def updateDisplay(self):
        if(self.displayUpdated): return
        self.displayUpdated = True
        #sort the players by amount of wins
        if(not(isSorted(self.mfpi, True))):
            sort(self.mfpi, True)
            #keep track of players' order and rank
            for i in range(len(self.mfpi)):
                self.order[self.mfpi[i].index] = i
                self.mfpi[i].rank = i + 1
        #rearrange the players according to the new order
        for i, j in enumerate(self.mfpi):
            for k in range(3):
                j.labels[k].grid_configure(row = i)
            j.updateLabel(self.NOGames)
        self.progressBar.updateFP(self.NOGames, settings["gpm"])
        #update the toplevel
        if(self.toplevelDisplayed):
            for i in range(4):
                tl = self.trendlines[i]
                wins_i = self.mfpi[i].wins
                self.canvas.coords(tl[0],
                                   *self.mfpi[i].coords)
                self.canvas.coords(tl[1],
                                   *MatchFrame.gtc(0, wins_i),
                                   self.mfpi[i].coords[-2],
                                   self.mfpi[i].coords[-1])
                self.canvas.coords(tl[2],
                                   self.MARGIN[0]//2,
                                   MatchFrame.gtc(None, wins_i))
                self.canvas.itemconfigure(tl[2], text = str(wins_i))

    def getPlayerInfos(self, indices = (0, 1, 2, 3)):
        return [self.mfpi[self.order[i]] for i in indices]
    def getTopPlayers(self, howMany = 2):
        return [(self.mfpi[i].name,
                 self.mfpi[i].path,
                 self.mfpi[i].id) for i in range(howMany)]
    def getData(self):
        data = []
        n = strings["BotName"].ljust(15)
        w = strings["Wins"].ljust(6)
        i = "ID     "
        data.append(''.join((n, w, i)))
        for m in self.mfpi:
            n = m.name.ljust(15)
            w = str(m.wins).ljust(6)
            i = m.id.ljust(7)
            data.append(''.join((n, w, i)))
        return '\n'.join(data)
    #called after each game, winner is index of the player who won
    def newWin(self, winner):
        self.displayUpdated = False
        self.mfpi[self.order[winner]].wins += 1
        self.NOGames += 1
        newPixel = MatchFrame.gtc(self.NOGames)
        #if a new pixel should be added to trendlines on canvas
        if(newPixel != self.mfpi[0].coords[-2]):
            for i in range(len(self.mfpi)):
                self.mfpi[i].coords.append(newPixel)
                self.mfpi[i].coords.append(MatchFrame.gtc(None,
                                                          self.mfpi[i].wins))

#similar to MFPlayerInfo, but not enough to inherit anything
#possible feature: making MatchFrame accept arbitrary number of players
#which can be shown or hidden in TopLevel and that TopLevel can display
#charts for other sorting options as well
class LVPlayerInfo(object):
    def __init__(self, master, info):
        self.name, self.path, self.id = info
        self.labels = [tk.Label(master,
                                text = self.name,
                                width = 14,
                                fg = self.id,
                                bd = 1,
                                font = FONTS["smaller"]), #name
                       tk.Label(master,
                                text = "0",
                                width = 4,
                                bd = 1,
                                font = FONTS["smaller"]), #wins
                       tk.Label(master,
                                text = "0",
                                bd = 1,
                                font = FONTS["smaller"]), #pts
                       tk.Label(master,
                                text = "0",
                                bd = 1,
                                font = FONTS["smaller"])] #avg rank
        self.wins = 0
        self.pts = 0
        self.pfp = [settings["ptsForPlace#" + str(i + 1)] for i in range(4)]
        self.sumOfRanks = 0
        self.matches = []
        #let's hope noone will change this while sorting
        #attiribute used for comparing players, index for __getitem__()
        self.compAttr = 0
    def addMatch(self, match):
        assert self.id == match.id
        self.matches.append(match)
    def updateLabels(self):
        for i in range(3):
            self.labels[i+1].config(text = str(int(self[i])))
    def updateStats(self):
        self.wins = self.pts = self.sumOfRanks = 0
        for mfpi in self.matches:
            self.wins += mfpi.wins
            self.pts += self.pfp[mfpi.rank-1]
            self.sumOfRanks += mfpi.rank
    def __getitem__(self, key):
        #defined to make __ge__ & __le__ more compact
        if(key == 0):   return self.wins
        elif(key == 1): return self.pts
        elif(key == 2): return self.sumOfRanks / len(self.matches)
        else:           raise IndexError
    def __ge__(self, other):
        return self[self.compAttr] >= other[self.compAttr]
    def __le__(self, other):
        return self[self.compAttr] <= other[self.compAttr]

#handles matches in separate processes
#q - multiprocessing.Queue, queue for output to main thread
#matchIDs - iterable of ints, to tell apart outputs from different matches
#matchKwargs - iterable of dictionares, arguments for core.Game.__init__()
#gpm - int, games per match
#ppos - int, 0: player order is constant
#            1: players change relative order every 1/6 of match
#            2: players change positions randomly every match
def matchHandler(q, matchIDs, matchKwargs, gpm, ppos):
    #keeps track of order around table
    if(ppos):
        ordering = [list(range(4)) for i in range(len(matchIDs))]
    games = []
    for i in range(len(matchIDs)):
        games.append(core.Game(**matchKwargs[i]))
    #gave away a bit of performance for "balanced" match processing
    #swap next two lines for better performance
    for i in range(gpm):
        for j in range(len(matchIDs)): #len() is O(1)
            if(ppos == 1 and  (True if gpm < 6 else i % (gpm // 6) == 0)):
                newOrder = SHUFFLE[6* i // gpm if gpm > 6 else i]
                ordering[j] = [ordering[j][k] for k in newOrder]
                winner = games[j].start(newOrder)
            elif(ppos == 2):
                newOrder = [0, 1, 2, 3]
                shuffle(newOrder)
                ordering[j] = [ordering[j][k] for k in newOrder]
                winner = games[j].start(newOrder)
            else:
                winner = games[j].start()
            if(ppos): #to make winner's index consistent for main thread
                winner = ordering[j][winner]
            q.put((matchIDs[j], winner))

class LeagueView(View):
    GROUPS = ((0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11), (12, 13, 14, 15),
              (0, 4, 8, 12), (1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15),
              (0, 5, 10, 15), (1, 4, 11, 14), (2, 7, 8, 13), (3, 6, 9, 12),
              (0, 6, 11, 13), (1, 7, 10, 12), (2, 4, 9, 15), (3, 5, 8, 14),
              (0, 7, 9, 14), (1, 6, 8, 15), (2, 5, 11, 12), (3, 4, 10, 13))
    def __init__(self, viewName, nextViewName, intent, *args, **kwargs):
        View.__init__(self, viewName, nextViewName, *args, **kwargs)
        self.cSpan(5)
        #Frame on the right displaying overall player stats
        self.playerStatsFrame = tk.Frame(self, bd = 1, relief = tk.SOLID)
        self.playerStatsFrame.grid(row = 1,
                                   column = 4,
                                   rowspan = 5,
                                   pady = 10,
                                   sticky = tk.N + tk.S)
        #refresh period in s
        self.rp = 1.0 / settings["fps"]
        #index and direction of sorting lvpi
        self.isDesc = True
        self.sortBy = 0
        #lvpi background colours
        self.bgc = (COLOURS["ma"], COLOURS["la"])
        self.lvpi = []
        for i, j in enumerate(intent):
            #gridding lvpis
            self.playerStatsFrame.rowconfigure(i + 1, weight = 1)
            self.lvpi.append(LVPlayerInfo(self.playerStatsFrame, tuple(j)))
            for k in range(len(self.lvpi[-1].labels)):
                self.lvpi[-1].labels[k].config(bg = self.bgc[i % 2])
                self.lvpi[-1].labels[k].grid(row = i + 1,
                                             column = k,
                                             sticky = tk.NE + tk.SW)
        self.nameLabel = tk.Label(self.playerStatsFrame,
                                  text = strings["BotName"],
                                  bg = COLOURS["da"],
                                  fg = COLOURS["bg"])
        self.nameLabel.grid(row = 0, column = 0, sticky = tk.NE + tk.SW)
        self.sortBtns = []
        for i, j in enumerate(("Wins", "Pts", "AvgPos")):
            self.sortBtns.append(tk.Label(self.playerStatsFrame,
                                          text = strings[j],
                                          width = 8,
                                          bg = COLOURS["da"],
                                          fg = COLOURS["bg"],
                                          relief = tk.FLAT))
            self.sortBtns[-1].bind("<Button-1>", self.changeSort)
            self.sortBtns[-1].grid(row = 0,
                                   column = i + 1,
                                   sticky = tk.NE + tk.SW)
        self.sortBtns[0].config(relief = tk.RAISED)
        self.playerStatsFrame.rowconfigure(0, weight = 1)
        self.matchFrames = []
        for i in range(5):
            self.rowconfigure(i + 1, weight = 1)
            self.columnconfigure(i, weight = 1)
        #Creating MatchFrames
        for i in range(len(LeagueView.GROUPS)):
            self.matchFrames.append(MatchFrame([
                tuple(intent[LeagueView.GROUPS[i][j]])
                for j in range(4)], self))
            #Populating the lvpi with mfpis from matchFrames
            for j, player in enumerate(self.matchFrames[-1].getPlayerInfos()):
                self.lvpi[LeagueView.GROUPS[i][j]].addMatch(player)
            self.matchFrames[-1].grid(row = i // 4 + 1, column = i % 4)
        self.lastRefreshed = time()
        #Creating processes: similar to TournamentView
        self.availableCores = multiprocessing.cpu_count() - 1 or 1
        self.processes = []
        q = multiprocessing.Queue()
        matchIDs = [[] for i in range(self.availableCores)]
        for i in range(len(self.matchFrames)):
            matchIDs[i % self.availableCores].append(i)
        #to avoid string comparison in matchHandler
        ppToInt = SETTINGS_PP.index(settings["pp"])
        for i in range(self.availableCores):
            kw = [dict(modules = [intent[LeagueView.GROUPS[k][j]][1]
                                         for j in range(4)],
                       MIOCmod = settings["mod"] == "On")
                       for k in range(len(matchIDs[i]))]
            self.processes.append(multiprocessing.Process(
                target = matchHandler,
                args = (q,
                        matchIDs[i],
                        kw,
                        settings["gpm"],
                        ppToInt)))
            self.processes[-1].start()
        broadcastReceiverThread = Thread(target = self.receiveBroadcast,
                                         args = (q, ))
        broadcastReceiverThread.start()
        self.focus_set()
        self.bind("<Control-s>", self.export)

    def export(self, event):
        filename = strftime("%c").replace(' ', '_').replace(':', '-') + ".txt"
        data = []
        n = strings["BotName"].ljust(15)
        w = strings["Wins"].ljust(6)
        p = strings["Pts"].ljust(7)
        a = strings["AvgPos"].ljust(10)
        i = "ID     "
        data.append(''.join((n, w, p, a, i)))
        for l in self.lvpi:
            n = l.name.ljust(15)
            w = str(l[0]).ljust(6)
            p = str(l[1]).ljust(7)
            a = str(l[2])[:9].ljust(10)
            i = l.id.ljust(7)
            data.append(''.join((n, w, p, a, i)))
        with open(filename, 'w') as file:
            file.write('\n'.join(data))
            file.write("\n\n\n")
            for i in range(len(self.matchFrames)):
                mn = "Match #" + str(i) + "\n"
                file.write(mn)
                file.write(self.matchFrames[i].getData())
                file.write('\n\n')

    def changeSort(self, event):
        col = event.widget.grid_info()["column"] - 1
        if(self.sortBy == col):
            self.isDesc = not(self.isDesc)
        else:
            self.sortBtns[self.sortBy].config(relief = tk.FLAT)
            self.sortBy = col
            self.isDesc = (col != 2)
            for i in self.lvpi:
                i.compAttr = col
        event.widget.config(relief = tk.RAISED if self.isDesc else tk.SUNKEN)

    def receiveBroadcast(self, q):
        gamesTotal = len(self.matchFrames) * settings["gpm"]
        gameNumber = 0
        #receiving game results
        while(gameNumber < gamesTotal and not(self.isDestroyed)):
            matchID, winner = q.get()
            self.matchFrames[matchID].newWin(winner)
            gameNumber += 1
            #if it's time to refresh the screen
            if(time() - self.lastRefreshed > self.rp):
                #update matchFrames, than update lfpi
                for i in self.matchFrames:
                    i.updateDisplay()
                for i in self.lvpi:
                    i.updateStats()
                    i.updateLabels()
                if(not(isSorted(self.lvpi, self.isDesc))):
                    sort(self.lvpi, self.isDesc)
                for i, j in enumerate(self.lvpi):
                    for k in range(len(j.labels)):
                        j.labels[k].config(bg = self.bgc[i % 2])
                        j.labels[k].grid_configure(row = i + 1)
                #rearrange the player frames and update info
                self.lastRefreshed = time()
        #closing the processes and updating matchFrames if needed
        if(not(self.isDestroyed)):
            for i in self.processes:
                if(i.is_alive()):
                    i.join()
                    i.close()
            for mf in self.matchFrames:
                mf.updateDisplay()
        else:
            for i in self.processes:
                if(i.is_alive()):
                    i.terminate()



def isLight(color):
    rgb = [int(color[i:i+2], 16) for i in range(1, 7, 2)]
    return sum(rgb) > 400 or rgb[1] > 200

def isSorted(arr, reverse = False):
    for i in range(1, len(arr)):
        if(not((arr[i] >= arr[i - 1] or reverse) and
               (arr[i] <= arr[i - 1] or not(reverse)))):
            return False
    return True
def sort(arr, reverse = False): #if reverse highest to lowest
    def qsort(arr, l, r, rev):
        if(l >= r):
            return
        pivot = arr[r]
        cnt = l
        for i in range(l, r + 1):
            if((pivot >= arr[i] and not(rev)) or (pivot <= arr[i] and rev)):
                arr[i], arr[cnt] = arr[cnt], arr[i]
                cnt += 1
        qsort(arr, l, cnt - 2, rev)
        qsort(arr, cnt, r, rev)
    qsort(arr, 0, len(arr) - 1, reverse)
    return arr

def updateStrings(widget):
    for view in filter(lambda w: (issubclass(type(w), View)), widget.winfo_children()):
        view.updateTextViews()
        updateStrings(view)

def load(fileName):
    if(fileName == "images"):
        global images
        for i in IMAGE_NAMES:
            images[i] = tk.PhotoImage(file = "res/drawables/" + str(i) +  ".png")
        return
    global settings, strings
    with open("res/" + fileName + ".txt", "r", encoding = "utf-8") as file:
        for i in file:
            if(i[:-1]):
                key, value = i[:-1].split("|")
                if(fileName == "settings"):
                    settings[key] = int(value) if value.isdigit() else value
                else:
                    strings[key] = value

def getView(viewKey, intent, currentView):
    return VIEWS[viewKey][1](viewName = viewKey,
                             nextViewName = VIEWS[viewKey][0],
                             intent = intent,
                             master = currentView)

IMAGE_NAMES = ["back", "fb", "ff", "pause", "play", "resume", "save", "transparent", "settings"] \
            + ["dice/" + str(i + 1) for i in range(6)] \
            + ["pieces/" + str(i) + str(j) for i in range(5) for j in range(4)]
VIEWS = {"Main Menu" : (("Play", "Settings", "Info"), MenuView), \
         "Info" : ((None,), InfoView), \
         "Play" : (("Single Game", "Tournament", "League"), MenuView), \
         "Single Game" : (("Board",), SelectBotsView), \
         "Board" : (("Results",), BoardView), \
         "Settings" : ((None,), SettingsView), \
         "Tournament" : (("TournamentView",), SelectBotsView), \
         "League" : (("LeagueView",), SelectBotsView), \
         "TournamentView" : (("Results",), TournamentView), \
         "LeagueView" : (("Results",), LeagueView) }
if(__name__ == "__main__"):
    mainWindow = tk.Tk()
    mainWindow.tk_setPalette(activeBackground = COLOURS["da"],
                             activeForeground = COLOURS["bg"],
                             background = COLOURS["bg"],
                             disabledForeground = COLOURS["fg"],
                             foreground = COLOURS["fg"],
                             highlightBackground = COLOURS["bg"],
                             highlightColor = COLOURS["la"],
                             insertBackground = "red",
                             selectColor = COLOURS["da"],
                             selectBackground = "red",
                             selectForeground = COLOURS["bg"],
                             troughColor = COLOURS["ma"])
    settings = dict()
    strings = dict()
    images = dict()
    load("settings")
    load("strings/" + settings["lang"])
    imageLoadingThread = Thread(target = load, args = ("images", ))
    imageLoadingThread.start()
    mainMenu = getView("Main Menu", None, mainWindow)
    mainWindow.mainloop()
