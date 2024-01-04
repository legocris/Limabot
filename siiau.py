from html.parser import HTMLParser
from urllib import request
import ssl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors 
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
    #CU    NRC     Clave   Materia     Sec     CR  CUP     DIS     Ses/Hora/Dias/Edif/Aula/Periodo     Ses/Profesor
    Prop = { "CU":0, "NRC":1, "Clave":2, "Materia":3, "Sec":4, "CR":5, "CUP":6,"DIS":7, "Horario":8, "Profesor":9}
    Horarios = { "Ses":0, "Hora":1, "Dias":2, "Edif":3, "Aula":4, "Periodo":5 }
    Profesor = { "Ses":0, "Profesor":1}

    def __init__(self, datos, baseDatos):
        #datos es el dato especifico de esta clase.
        #baseDatos es el objeto en que se almacena la base de datos de todas las clases

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
        self.baseDatos = baseDatos
        self.datos = datos

        baseDatos.NRCDict[ self.getNRC() ] = self

        if self.getClave() not in baseDatos.ClaveDict:
            baseDatos.ClaveDict[ str(self.getClave())  ] = {}

        baseDatos.ClaveDict[ str(self.getClave()) ][self.getNRC()] = self
            

    def get(self, prop):
        p = Clase.Prop[prop]
        return self.datos[p]

    def getMateria(self):
        return( self.datos[3] )

    def getNombre(self):
        return self.getMateria()
    
    def getSiglas(self):
        return "".join( [l[0] for l in self.getMateria().split() if (l!= "DE" and l!="DEL") ]  )
    
    def getProfesorCorto(self):
        return " ".join( self.getProfesor().split()[-2:] )

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
    
    def getCoordenadas(self):
        coordenadas = []
        for h in self.getHorarios():
            dias = h[Clase.Horarios["Dias"] ]
            hora = h[Clase.Horarios["Hora"] ]
            
            for j in range( len(dias)//2 ):
                if dias[j*2] == '.':
                    continue
                
                for i in range(int(hora[:2]), int(hora[5:7])+1):
                    coordenadas.append( (i-7, j) )
        
        return coordenadas
                

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
    
    def imprime(self):
      return( "nrc: " + self.getNRC()    + "\n" +
              "clv: " + self.getClave()    + "\n" +
              "Nom: " + self.getNombre()     + "\n" +
              "Pro: " + self.getProfesor() + "\n"   )
    
    def __str__(self):
      return str(self.datos)

    def isClave( code ):
        return ( type(code)==str and code[0]=='I' )
    
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
    
    def solapan(lista):
        return lista.pop().solapanConmigo(lista)

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
        ax.text( np.cos(a1), np.sin(a1), lista[i].getSiglas()+" "+lista[i].getNRC()+'\n'+lista[i].getProfesorCorto(), horizontalalignment="center")
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

def getColor(indice, total, sat=0.8, val=0.9):
    # Define HSV color values
    hsv_color = (float(indice)/float(total), sat, val)

    # Convert HSV to RGB
    rgb_color = np.array(hsv_color)
    rgb_color = np.clip(rgb_color, 0, 1)
    rgb_color = colors.hsv_to_rgb(rgb_color)  # Use colors.hsv_to_rgb for conversion
    
    return rgb_color

def GraficarCalendario( lista, show=False ):
    # Create a list of hours
    hours = [str(h)+":00" for h in range(7, 21)]

    # Create a list of days
    days = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]

    # Create a list of lists to store colors as strings
    colors = [["white"] * len(days) for _ in hours]  # Initialize all cells as white
    textos = [[""] * len(days) for _ in hours]  # Initialize all cells as white

    for i, clase in enumerate(lista):
        for coordenada in clase.getCoordenadas():
            if (coordenada[0]<0): continue #Los horarios virtuales tienen coordenadas negativas
            
            if textos[coordenada[0]][coordenada[1]] == "":
                colors[coordenada[0]][coordenada[1]] = getColor(i, len(lista))
                textos[coordenada[0]][coordenada[1]] += clase.getSiglas()
            else:
                colors[coordenada[0]][coordenada[1]] = getColor(i, len(lista), sat=0.0, val=0.8)
                textos[coordenada[0]][coordenada[1]] += "|"+clase.getSiglas()
            
            sat = 0.8


    # Fill in the colors of the cells according to the topics
    #colors[4][0]  = "blue"  # Maths on Mondays and Wednesdays, 10:00-12:00
    #colors[0][0] = '#C7A2C8'

    # Add more color assignments for other topics

    # Create the plot
    fig, ax = plt.subplots()

    # Create the table
    table = ax.table(cellText=textos, rowLabels=hours, colLabels=days, loc="center", cellLoc='center', cellColours=colors)

    # Set the table properties
    table.set_fontsize(10)
    table.scale(1, 1.5)  # Adjust cell size

    # Remove the table frame
    #table._cells.set_edgecolor("white")
    #for cell in table.get_celld().values():
    #    cell.set_edgecolor("white")


    # Set the title
    ax.set_title("Calendario Semanal")
    ax.axis('off')

    # Adjust layout
    #plt.tight_layout()

    # Show the plot
    #plt.show()

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


class BaseDatos():
    def __init__(self, ciclo = "202320"):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = "https://siiauescolar.siiau.udg.mx/wal/sspseca.consulta_oferta?ciclop="+ciclo+"&cup=&majrp=LIMA&mostrarp=100000"
        body=request.urlopen(url, context=ctx).read()
        Datos = []

        parser = ParserUDG()
        parser.feed_datos( str(body), Datos )

        self.Datos = Datos[0]

        self.NRCDict = {}
        self.ClaveDict = {} 

        self.Clases = [Clase(d, self) for d in self.Datos]
        limpia(self.Clases)

        self.malla={
                'primero': ["I5919", "I5920", "I5921", "I5922", "I5923", "I5924", "I5940"],
                'segundo': ["I5978", "I5926", "I5927", "I5928", "I5929", "I5937", "I5950"],
                'tercero': ["I5925", "I5945", "I5946", "I5930", "I5931"],
                'cuarto': ["I5941", "I5969", "I5970", "I5951", "I5952", "I5936"],
                'quinto': ["I5948", "I5932", "I5933", "I5955", "I5956", "I5966"],
                'sexto': ["I5942", "I5960", "I5934", "I5935", "I5953", "I5954", "I5967", "I5968"],
                'septimo': ["I5943", "I5979", "I5961", "I5962", "I5938", "I5939", "I5971", "I5944"],
                'octavo': ["I5947", "I5963", "I5964", "I5957", "I5958", "I5949", "I5965"],
                'noveno': ["I5959", "I5972"],
                'optativas': ["I5978","I5979", "I5972"],
                'optativisimas': ["I5982","I5981","I5977","I5976", "I5980"],
                'todo': list(self.ClaveDict.keys())
                }


    def findNRC(self, nrc):
        if ( type(nrc) == list ):
            return [self.find(i) for i in nrc]
        return self.NRCDict[nrc]

    def findClave(self, clave):
        if ( type(clave) == list ):
            l = []
            for c in clave:
                l += list( self.ClaveDict[c].values() )
            return l
        return list( self.ClaveDict[clave].values() )

    def findNested(self, code):
        if ( type(code) == list ):
            return [ self.find(i) for i in code]
        return self.find(self.malla[code]) if code in self.malla else self.findClave(code) if Clase.isClave(code) else self.findNRC(code)

    def find(self, code ):
        return unnest( self.findNested( code ) )


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