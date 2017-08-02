Grupo 03
Joao Esteves	78304
Manuel Santos	78445
Joao Castanho	79679

#0 Passo

unzip proj_3.zip
cd proj_3

#1 Passo

cd tcs/
python3 tcs.py [-p TCSport]

#2 Passo

cd trs/
python3 trs.py language  [-p TRSport]  [-n TCSname] [-e TCSport]

#3 Passo

cd user/
python3 user.py [-n TCSname] [-p TCSport]


Para testar a troca de ficheiros de imagem usar:

first.jpg
chewy.jpg
falcon.jpg
r2d2.jpg
deathstar.jpg

Para testar a troca de texto usar (alguns exemplos):

engineering
science
fiber
optics
math