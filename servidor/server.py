#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Este archivo procesa los datos en la tabla crudo y los inserta
# en las tablas correspondientes para que luego los otros agentes ejecuten
# las distintas acciones.


import select
import os
from time import sleep
from XVM import *
from db import *

os.system("clear")
DB = db()
while(1):
	sleep(1)
	# Comienzo a consultar todos los movimientos que no han sido procesados
	rs = DB.sqlSelect("id,info,host,port","crudo","levantado=0")
	#restantes=rs.rowcount

	for id,info,host,port in rs.fetchall():
		#print "Informacion recibida! - Restantes %s" % restantes
		#print info
		paquete=info.split(";") # El nombre de los datos

		# Variables Comunes a todos los tipos de dato
		id_virloc=paquete[1].replace("ID=","")
		nromensaje=paquete[2]
		checksum=paquete[3]

		

		# Actualizo los datos del equipo
		DB.sqlInsertOrUpdate('equipos','id=%s,ip="%s",puerto=%s' % (id_virloc,host,port),'ip="%s",puerto=%s' % (host,port))
		array=paquete[0].split(",")
		print info
		# Selecciono el tipo de paquete
		if info[0:4]==">RUS":
			if info[4:6]=="01":
				print "LogIn de chofer"
				chofer=array[2].replace("-","")

				# Aca comienza la logica sobre la habilitacion del chofer
				# Deberia haber una funcion que verifique el estado del chofer
				choferhabilitado=1
				if choferhabilitado==1:
					print "Chofer habilitado"
					xvm=XVM()
					xvm.sendMsgToQueue(id_virloc,"SSH001",0)
					DB.sqlUpdate('equipos','chofer=%s' % chofer,'id=%s' % id_virloc)
				else:
					print "Chofer NO HABILITADO"
			if info[4:6]=="02":
				print "Esto es un pago en efectivo"
				fecha="20%s-%s-%s %s:%s:%s" % (array[1][4:6],array[1][2:4],array[1][0:2],array[1][6:8],array[1][8:10],array[1][10:12])
				chofer=array[2].replace("-","")
				tiempo=array[3].replace("-","")
				distancia=array[4].replace("-","")
				monto=array[6].replace("-","")

				cadena="fecha='%s',id_chofer=%s,monto=%s,id_virloc=%s,tipo_cobro='EFECTIVO',tiempo=%s,distancia=%s,estado='OK'" % (fecha,chofer,monto,id_virloc,tiempo,distancia)
				DB.sqlInsert('pagos',cadena)
				estado="EN SERVICIO"
				DB.sqlInsertOrUpdate('equipos','id=%s,estado="%s"' % (id_virloc,estado),'estado="%s"' % estado)


			if info[4:6]=="03":
				if array[8]=="3":
					print "COBRANDO con TARJETA"
					fecha="20%s-%s-%s %s:%s:%s" % (array[1][4:6],array[1][2:4],array[1][0:2],array[1][6:8],array[1][8:10],array[1][10:12])
					chofer=array[2].replace("-","")
					tiempo=array[3].replace("-","")
					distancia=array[4].replace("-","")
					cuenta=array[5].replace("-","")
					password=array[6].replace("-","")
					monto=array[7].replace("-","")
					cadena='fecha="%s",cuenta="%s",id_chofer=%s,monto=%s,id_virloc=%s,tipo_cobro="TARJETA",tiempo=%s,distancia=%s,estado="PENDING",password=%s' % (fecha,cuenta,chofer,monto,id_virloc,tiempo,distancia,password)
					DB.sqlInsert('pagos',cadena)
				if array[8]=="2":
					print "COBRANDO con WALLET"
					array=paquete[0].split(",")
					fecha="20%s-%s-%s %s:%s:%s" % (array[1][4:6],array[1][2:4],array[1][0:2],array[1][6:8],array[1][8:10],array[1][10:12])
					chofer=array[2].replace("-","")
					tiempo=array[3].replace("-","")
					distancia=array[4].replace("-","")
					cuenta=array[5].replace("-","")
					password=array[6].replace("-","")
					monto=array[7].replace("-","")
					cadena='fecha="%s",cuenta=%s,id_chofer=%s,monto=%s,id_virloc=%s,tipo_cobro="WALLET",tiempo=%s,distancia=%s,estado="PENDING",password="%s"' % (fecha,cuenta,chofer,monto,id_virloc,tiempo,distancia,password)
					DB.sqlInsert("pagos",cadena)

		if info[0:4]==">RGP" or info[0:4]==">RTT":
			estado=""
			evento=""
			#print "Informacion de posicion"
			tipo=paquete[0][1:4]
			fecha=paquete[0][4:10]
			hora=paquete[0][10:16]
			datetime="20%s-%s-%s %s:%s:%s" % (fecha[4:6],fecha[2:4],fecha[0:2],hora[0:2],hora[2:4],hora[4:6])
			latitud=float(paquete[0][16:24])/100000
			longitud=float(paquete[0][24:33])/100000
			velocidad=paquete[0][33:36]
			rumbo=paquete[0][36:39]
			tipopos=paquete[0][39:40]
			age=paquete[0][40:42]
			ent=paquete[0][42:44]
			numero_evento=paquete[0][44:46]
			errorgps=paquete[0][46:48]
			#print "Fecha %s Hora GMT %s - Vehiculo %s - Tipo %s localizado en %s %s a %s kms/h con rumbo %s" % (fecha,hora,id_virloc,tipo,latitud,longitud,velocidad,rumbo)
			DB.sqlInsertOrUpdate('equipos','id=%s,ip="%s",puerto=%s,latitud="%s",longitud="%s",velocidad=%s,rumbo=%s' % (id_virloc,host,port,latitud,longitud,velocidad,rumbo),'ip="%s",puerto=%s,latitud="%s",longitud="%s",velocidad=%s,rumbo=%s' % (host,port,latitud,longitud,velocidad,rumbo))
			DB.sqlInsert('posiciones','id_virloc=%s,host="%s",port=%s,latitud="%s",longitud="%s",velocidad=%s,rumbo=%s' % (id_virloc,host,port,latitud,longitud,velocidad,rumbo))

			evento=info[44:46]
			if evento=="15":
				estado="EN SERVICIO"

			if evento=="16":
				estado="FUERA DE SERVICIO"

			if evento=="20":
				estado="ON-LINE"

			if evento=="22":
				estado="OFF-LINE"

			if evento=="25":
				estado="EN VIAJE"

			if evento=="26":
				estado="OCUPADO"
				#Aca que deberia hacer? porque el estado deberia ser "en viaje" con su codigo de viaje o algo asi

			if evento=="27":
				estado="VEHICULO RECHAZA VIAJE"
				#Aca que deberia hacer? porque el estado deberia ser "en viaje" con su codigo de viaje o algo asi

			if evento=="28":
				estado="VIAJE FINALIZADO"
				#Aca que deberia hacer? porque el estado deberia ser "en viaje" con su codigo de viaje o algo asi

			if estado<>"":
				print "Cambio de estado vehiculo %s a estado %s" % (id_virloc,estado)
				DB.sqlInsertOrUpdate('equipos','id=%s,estado="%s"' % (id_virloc,estado),'estado="%s"' % estado)


		DB.sqlUpdate('crudo','levantado=1','id=%s' % id)
		#restantes=restantes-1
		print "-" * 80
