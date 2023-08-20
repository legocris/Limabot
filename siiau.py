from html.parser import HTMLParser
from urllib import request
import ssl
import numpy as np
import matplotlib.pyplot as plt
import tempfile


def limpia(lista):
    i=0
    while ( i<len(lista) ):
        if type(lista[i])==list:
            if ( limpia(lista[i])==0 ):
                del lista[i]
                i-=1
        i+=1
    return len(lista)

def unnest(lista):
    if type(lista) != list:
        return lista
    
    l = []
    for i in lista:
        l += unnest(i) if type(i) == list else [i]
    return l

#Esto es lo feo del programa, pero también lo más importante. Comvierte el AJQUEROSO html del siiau a clases legibles.
class ParserUDG(HTMLParser):
    lastTag = ""
    lastClass = ""
    i = 0
    datos = []
    #Primero son todas las funciones relevantes del parser
    def handle_starttag(self, tag, attrs):
        self.lastTag = tag
        self.lastClass = ""
        for attr in attrs:
            #print("     attr:", attr)
            if ( attr[0]=='class' ):
                self.lastClass = attr[1]

        #if ( tag=="td" ):
            #print("Start tag:", tag)

        if ( tag=='table' ):
            d = self.datos
            for j in range(self.i):
                d=d[-1]
            d.append([]);
            self.i+=1

        if ( tag=='tr' ):
            d = self.datos
            for j in range(self.i):
                d=d[-1]
            d.append([]);
            self.i+=1

    def handle_endtag(self, tag):
        self.lastTag = ""
        self.lastClass = ""
        if ( tag=='table' ):
            self.i-=1
        if ( tag=='tr' ):
            self.i-=1

    def handle_data(self, data):
        if ( self.lastTag == "td" and data!='' and data[0]!='\\' and data.isascii() ):
            d = self.datos
            for j in range(self.i):
                d=d[-1]
            d.append(data)

        if ( self.lastTag == "a" ):
            d = self.datos
            for j in range(self.i):
                d=d[-1]
            d.append(data)

    #Esta función es aparte y es la que usamos
    def feed_datos(self, str, datos):
        self.datos = datos
        self.feed(str)

        #Limpiar cosas vacías
        #limpia(datos) #Quizá es mejor no

class Clase():
    NRCDict = {}
    ClaveDict = {} 
    #CU    NRC     Clave   Materia     Sec     CR  CUP     DIS     Ses/Hora/Dias/Edif/Aula/Periodo     Ses/Profesor
    Prop = { "CU":0, "NRC":1, "Clave":2, "Materia":3, "Sec":4, "CR":5, "CUP":6,"DIS":7, "Horario":8, "Profesor":9}
    Horarios = { "Ses":0, "Hora":1, "Dias":2, "Edif":3, "Aula":4, "Periodo":5 }
    Profesor = { "Ses":0, "Profesor":1}

    def __init__(self, datos):
        #Revisar que el formato esté bien
        try:
            if (len(datos) != len(Clase.Prop)):
                print("("+str(len(datos))+")"+"Error de formato en clase: "+str(datos))
                if len(datos) == 0:
                    print("Clase vacia descartando")
                    return

            if ( type(datos[8]) != list ):
                 print("Clase NRC."+datos[1]+" sin datos de horario, se considerarán vacios")
                 datos[8] = [["" for i in range(len(Clase.Horarios))]]

            for horario in datos[8]:
                if ( type(horario) != list ):
                    print("Clase NRC."+str(datos[1])+" error en datos de horario, se considerarán vacios")
                    horario = ["" for i in range(len(Clase.Horarios))]
                    continue
                if (len(horario) != len(Clase.Horarios)):
                    print("Clase NRC."+str(datos[1])+" faltan datos de horario, se considerarán vacios")
                    horario += ["" for h in range(len(Clase.Horarios)-len(horario))]

            if ( type(datos[9]) != list ):
                 print("Clase NRC."+datos[1]+" sin datos de Profesor, se considerarán vacios")
                 datos[9] = [["" for i in range(len(Clase.Profesor))]]

            for profesor in datos[9]:
                if ( type(profesor) != list ):
                    print("Clase NRC."+str(datos[1])+" error en datos de horario, se considerarán vacios")
                    profesor = ["" for i in range(len(Clase.Profesor))]
                    continue
                if ( len(profesor) != len(Clase.Profesor) ):
                    print("Clase NRC."+datos[1]+" faltan datos de Profesor, se considerarán vacios")
                    profesor += ["" for h in range(len(Clase.Profesor)-len(profesor))]

        except:
            print("ERROR al dar formato a la clase con datos:")
            print(datos)
            return

        #Ahora sí lo importante, añadir a las estructuras de datos para que la clase sea encontrada
        self.datos=datos

        Clase.NRCDict[ self.getNRC() ] = self

        if self.getClave() not in Clase.ClaveDict:
            Clase.ClaveDict[ str(self.getClave())  ] = {}

        Clase.ClaveDict[ str(self.getClave()) ][self.getNRC] = self


            

    def get(self, prop):
        p = Clase.Prop[prop]
        return self.datos[p]

    def getMateria(self):
        return( self.datos[3] )

    def getName(self):
        return self.getMateria()

    def getNRC(self):
        return( self.datos[1] )

    def getClave(self):
        return( self.datos[2] )

    def getProfesor(self, n=0, arg="Profesor"):
        return self.datos[9][n][Clase.Profesor[arg]]

    def getHorario(self, n=0, arg="Dias"):
        return self.datos[8][n][Clase.Horarios[arg]]

    def getHorarios(self):
        return self.datos[8]

    def isClave( code ):
        return ( type(code)==str and code[0]=='I' )

    def findNRC(nrc):
        if ( type(nrc) == list ):
            return [Clase.find(i) for i in nrc]
        return Clase.NRCDict[nrc]

    def findClave(clave):
        if ( type(clave) == list ):
            l = []
            for c in clave:
                l += list( Clase.ClaveDict[c].values() )
            return l
        return list( Clase.ClaveDict[clave].values() )

    def findNested(code):
        if ( type(code) == list ):
            return [Clase.find(i) for i in code]
        return Clase.findClave(code) if Clase.isClave(code) else Clase.findNRC(code)


    def find( code ):
        return unnest( Clase.findNested( code ) )


    def coincidenDias(str1, str2):
        if (str1=='' or str2==''):
            return False

        for c1 in str1:
            if c1=="." or c1==" ":
                continue
            for c2 in str2:
                if (c1==c2):
                    return True
        return False

    def coincidenHoras(str1, str2):
        if (str1=='' or str2==''):
            return False
        a = str1.rsplit('-')
        b = str2.rsplit('-')

        return max( a[0], b[0] ) <= min(a[1], b[1])

    def solapa(self, otro):
        for horario in self.getHorarios():
            for otroHorario in otro.getHorarios():
                if ( Clase.coincidenDias(horario[2], otroHorario[2]) ):
                    #print("coinciden"+str(horario[2])+"-"+str(otroHorario[2]))
                    if ( Clase.coincidenHoras(horario[1], otroHorario[1]) ):
                        return True
        return False

    def solapanConmigo(self, lista):
        if len(lista)==0:
            return False

        for otro in lista:
            if ( self.solapa(otro) ):
                return True

        return lista.pop().solapanConmigo(lista)
        
    def solapan(lista):
        return lista.pop().solapanConmigo(lista)
    
    def imprime(self):
      return( "nrc: " + self.getClave()    + "\n" +
              "clv: " + self.getClave()    + "\n" +
              "Nom: " + self.getName()     + "\n" +
              "Pro: " + self.getProfesor() + "\n"   )
    
    def __str__(self):
      return str(self.datos)


def Graficar( lista, show=False ):
    fig = plt.figure(num=1, clear=True)
    #ax = plt.subplots(figsize=(6, 6))
    ax = fig.add_subplot()

    nx = 50
    ny = 50

    # Set up survey vectors
    xvec = np.linspace(-1, 1.0, nx)
    yvec = np.linspace(-1, 1.0, ny)

    # Set up survey matrices.  Design disk loading and gear ratio.
    x1, x2 = np.meshgrid(xvec, yvec)

    # Evaluate some stuff to plot
    obj = x1**2 + x2**2

    cntr = ax.contour(x1, x2, obj, [1], colors='black')
    #ax.clabel(cntr, fmt="%2.1f", use_clabeltext=True)

    N = len( lista )
    data = []
    for i in range(N):
        a1 = i*(2*np.pi)/N
        ax.text( np.cos(a1), np.sin(a1), lista[i].getName()+" "+lista[i].getNRC()+'\n'+lista[i].getProfesor(), horizontalalignment="center")
        ax.plot( np.cos(a1), np.sin(a1), "ro")
        for j in range(i+1, N):
            a2 = j*(2*np.pi)/N
            if not lista[i].solapa(lista[j]) and lista[i].getClave()!=lista[j].getClave():
                data += [(np.cos(a1), np.cos(a2)), (np.sin(a1), np.sin(a2))]

    ax.plot( *data)


    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.axis('off')



    # Create a temporary file to save the plot image
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        #Save the plot as a PNG image
        plt.gca().set_aspect('equal')
        plt.savefig(temp_file.name)
        print("Temporary file saved at:", temp_file.name)

        if (show):
            plt.show()

        fig.clear() #Cuidado con los memory leaks
        plt.close(fig)

        return temp_file.name

    

def GetDataBase( ciclo = "202320" ):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = "https://siiauescolar.siiau.udg.mx/wal/sspseca.consulta_oferta?ciclop="+ciclo+"&cup=&majrp=LIMA&mostrarp=100000"
    body=request.urlopen(url, context=ctx).read()
    Datos = []

    parser = ParserUDG()
    parser.feed_datos( str(body), Datos )

    Datos = Datos[0]

    Clases = [Clase(i) for i in Datos]
    limpia(Clases)

Datos = []
Clases = []


#GetDataBase()

# #Veamos si funciona buscando una clase por NRC

# #Probemos algunas funciones
# print("\n****PRUEBAS*****")
# print( a.getProfesor(0) )
# print( a.solapa( Clase.find("117741") ) )
# print( [clase.getNRC() for clase in Clase.findClave("I5921")]) #Imprime los NRC de las clases con Clave I5921
# print(a)

# #Se hace un Grafo de algunas clases, buscando por NRC y por clave
#Graficar( Clase.find(["57600", "I5969"]), True )


#["['D', '77404', 'I5969', 'ALGEBRA LINEAL NUMERICA', 'D01', '9', '15', '3', [['01', '1700-1855', 'L . . . . .', 'DEDV', 'LC01', '14/08/23 - 13/12/23'], ['01', '1700-1855', '. . I . . .', 'DEDV', 'A001', '14/08/23 - 13/12/23']], [['01', 'LICEA SALAZAR, JUAN ANTONIO']]]",
# "['D', '117741', 'I5969', 'ALGEBRA LINEAL NUMERICA', 'D02', '9', '16', '0', [['01', '1200-1355', '. . . . V .', '14/08/23 - 13/12/23', '', ''], ['01', '1300-1455', '. M . . . .', '14/08/23 - 13/12/23', '', '']], [['01', 'PLASCENCIA GARCIA, CRISTYAN JEOVANY']]]"]