from random import choice

start = [[10, 4], [4, 0], [0, 6], [6, 10]]

qt0 = [[10,4],[9,4],[8,4],[7,4],[6,4],[6,3],[6,2],[6,1],[6,0],[5,0]]
qt1 = [[4,0],[4,1],[4,2],[4,3],[4,4],[3,4],[2,4],[1,4],[0,4],[0,5]]
qt2 = [[0,6],[1,6],[2,6],[3,6],[4,6],[4,7],[4,8],[4,9],[4,10],[5,10]]
qt3 = [[6,10],[6,9],[6,8],[6,7],[6,6],[7,6],[8,6],[9,6],[10,6],[10,5]]
cilj = [[[9,5],[8,5],[7,5],[6,5]],[[5,1],[5,2],[5,3],[5,4]],[[1,5],[2,5],[3,5],[4,5]],[[5,9],[5,8],[5,7],[5,6]]]
bio = []
kucice = [[[9,0],[9,1],[9,2],[9,3]],[[1,0],[1,1],[1,2],[1,3]],[[1,7],[1,8],[1,9],[1,10]],[[9,7],[9,8],[9,9],[9,10]]]

def provjera_pomak(a, b, pozicije, d):
 if pozicije[a][b] in bio:
  c = bio.index(pozicije[a][b])
  if len(bio) - 4 + b >= c + d and not(bio[c+d] in pozicije[a]):
   return 1
 return 0
   
 


def main(pozicije, k, boja, dopustenePozicije):
  return choice(dopustenePozicije)
  global start, cilj, qt1, qt2, qt3, qt0, bio
  spawn = start[boja]
  if boja == 0:
   bio = qt0 + qt1 + qt2 + qt3 + cilj[0]
  elif boja == 1:
   bio = qt1 + qt2 + qt3 + qt0 + cilj[1]
  elif boja == 2:
   bio = qt2 + qt3 + qt0 + qt1 + cilj[2]
  else:
   bio = qt3 + qt0 + qt1 + qt2 + cilj[3]
  for i in range(4):
   if pozicije[boja][i] == kucice[boja][i] and k == 6 and not(start[boja] in pozicije[boja]):
    return "MIOC"[i]
   if provjera_pomak(boja, i, pozicije, k):
    return "MIOC"[i]
  return "0"
 
