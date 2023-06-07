from flask import Flask, render_template, request, session, redirect
import random
import mysql.connector


app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

#cambiar por la información de su BBDD--
db = mysql.connector.connect(
    host='localhost',
    user='user', 
    password='password',
    database='database'
)
#--------------------------------------
cursor = db.cursor()


@app.route('/', methods=['GET', 'POST'])
def index():
    session.pop('numero_aleatorio', None)
    session.pop('textos', None)
    return render_template('index.html')

@app.route('/reglas')
def reglas():
    return render_template('reglas.html')

@app.route('/jugar', methods=['POST'])
def jugar():
    nombre_jugador = request.form['nombre']
    session['nombre_jugador'] = nombre_jugador  # Almacenar el nombre en la sesión
    session['intentos'] = 0  # Inicializar el contador de intentos
    dificultad = request.form.get('dificultad')
    session['dificultad'] = dificultad
    textos = []
  
    numero_aleatorio = [] # lista donde se guardara el numero seleccionado aleatoriamente
    while len(numero_aleatorio) < 4:
        num = random.randint(0, 9) #condiciona que sean numeros del 0 al 9
        if num not in numero_aleatorio: #condiciona que no se repita ningun numero
            numero_aleatorio.append(num)
        session['numero_aleatorio'] = numero_aleatorio

    cursor.execute("INSERT INTO jugadores (nombre) VALUES (%s)", (nombre_jugador,))
    db.commit()

    return redirect('/adivinar')

@app.route('/puntuacion')
def puntuacion():

    cursor.execute("SELECT t1.id, t1.nombre, t1.puntaje FROM jugadores t1 INNER JOIN (SELECT nombre, MAX(puntaje) AS MaxPuntaje FROM jugadores GROUP BY nombre) t2 ON t1.nombre = t2.nombre AND t1.puntaje = t2.MaxPuntaje ORDER BY t1.puntaje DESC;")
    datos = cursor.fetchall()

    nombres_puntaje = {nombre: puntaje for _, nombre, puntaje in datos} #convierte a un diccionario la lista respuesta de la consulta sql
    return render_template('puntuacion.html', nombres_puntaje=nombres_puntaje)

@app.route('/adivinar', methods=['GET', 'POST'])
def adivinar():
    resultado = "Primer intento"
    numero_aleatorio = session.get('numero_aleatorio')
    intentos = session.get('intentos', 0)
    nombre_jugador = session['nombre_jugador']
    dificultad = session['dificultad']
    numero_no_valido = ""

    cursor.execute("SELECT puntaje FROM jugadores WHERE nombre = %s", (nombre_jugador,))
    puntaje_actual = cursor.fetchall()[0][0]
    if puntaje_actual is None:
        puntaje_actual = 0
    
    if 'nombre_jugador' not in session:
        return redirect('/')  # Redirigir al inicio si no se ha ingresado un nombre

    if request.method == 'POST':
        numero_ingresado = request.form['numero']

        lista_intento = list(numero_ingresado)
        lista_intento = [int(elemento) for elemento in lista_intento]

        if len(set(numero_ingresado)) != 4:
            numero_no_valido = "Las cifras deben ser diferentes entre sí."
            volver_a_jugar = False
        elif lista_intento == numero_aleatorio:

            # Incrementar el puntaje del jugador en la base de datos
            puntaje_nuevo = puntaje_actual + 1
            cursor.execute("UPDATE jugadores SET puntaje = %s WHERE nombre = %s", (puntaje_nuevo, nombre_jugador))
            db.commit()

            resultado = "¡Has acertado!"
            volver_a_jugar = True
            fijas = 4
            picas = 4

            session.pop('numero_aleatorio')
            session.pop('intentos')
        else:
            numero_no_valido = " "
            intentos += 1           
            volver_a_jugar = False
            fijas = 0
            picas = 0

            for numero in lista_intento:
                if numero in numero_aleatorio: #comparación de cada numero para determinar fijas y picas
                    posicion1 = lista_intento.index(numero)
                    posicion2 = numero_aleatorio.index(numero)
                    if posicion1 == posicion2:
                        fijas = fijas + 1                    
                    else:
                        picas = picas + 1
    
            if (dificultad == "dificil" and intentos == 5) or (dificultad == "medio" and intentos == 10) or (dificultad == "facil" and intentos == 20):
                resultado = "!Perdiste! el número era: "
                session.pop('numero_aleatorio')
                session.pop('intentos')
                
                if puntaje_actual > 0:
                    puntaje_nuevo = puntaje_actual - 1
                    cursor.execute("UPDATE jugadores SET puntaje = %s WHERE nombre = %s", (puntaje_nuevo, nombre_jugador))
                    db.commit()      
                
            texto = str(intentos) + " Intento: "+ str(numero_ingresado) + " --- Fijas: " + str(fijas) + " Picas: " + str(picas)
            if 'textos' not in session:
                session['textos'] = []
            session['textos'].append(texto)

        session['intentos'] = intentos
        
        return render_template('adivinar.html', resultado=resultado, volver_a_jugar=volver_a_jugar, numero_res=numero_aleatorio, numero_no_valido=numero_no_valido, textos=reversed(session.get('textos', [])))

    else:
        
        return render_template('adivinar.html', resultado=resultado, volver_a_jugar=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
