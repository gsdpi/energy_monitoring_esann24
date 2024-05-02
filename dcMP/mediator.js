
// MEDIATOR 

// Author: Diego García Pérez
// Descripción: Siguiendo las directrices de GoF (Gang Of Four), se propone la creación de un módulo que centralize la comunicación
// 			entre los módulo que forman nuestro dashboard. Este módulo recoge todos los eventos generados por los módulos y enlaza con los 
// 			callbacks, que el usuario indique. Este módulo contiene dos métodos para conseguir esta funcionalidad subcribe/publish.

// 			Con el fin de identificar univocamente los módulos a comunicar por Mediator se le asigna un identificador con init o con active 
// 			elements





function mediator(){

	//----------------------------------------------------------------------
	// Variables
	var activeElements = {},
		elementIndex,
		publish,	// Función de publicación de un evento
		subscribe,
		activeElements,
		desactiveElement,
		element;	// Función de subscripción de un evento

	var channels = {};  // Canales de comunicación 




	//----------------------------------------------------------------------
	// Private methods

	// _ sera el label 
	element = function(e,_){
		var keys;

		keys = Object.keys(e);

		this.function = e;
		for(var i=0; i< keys.length; i++){
			this[keys[i]] = e[keys[i]];
			
			if(keys[i] === "on"){
				console.log("creando callback");
				e.on(e.name,function(info){
					var type,
						params;

					type = info.type;
					params = info.arguments;

					publish(_ + "." + type, params);

				});
			}

		}

	}
	//----------------------------------------------------------------------
	//Public Methods	

	active = function(labels,closure){
		

		if(!arguments.length)
			return activeElements; 

		if (Array.isArray(closure)){
			
			// Detecting errors
			if (!Array.isArray(labels))
				throw Error("labels should be an array because clousures is an array");
			if (  typeof( closure[0] ) != "function" )
				throw Error("wrong type of active elements");
			if (closure.length != labels.length)
				throw Error("dimensions of labels and elements are not the same")
			if (typeof labels[0] != "string")
				throw Error("wrong type of labels")

			for(var i=0; i<closure.length; i++)
				activeElements[labels[i]] = new element(closure[i],labels[i]);


			elementIndex = Object.keys(activeElements);

			console.log("Created " + String(closure.length) + " new active elements")
			
			return this;

		}

		if(typeof(closure) != "function")
			throw Error("wrong type of active elements");			
		if (typeof labels != "string")
			throw Error("wrong type of label")

		activeElements[labels] = new element(closure,labels);
		elementIndex = Object.keys(activeElements);
		console.log("Created a new active element")
		return this;
		

	}


	desactiveElement = function(label){
		
		// Errors
		if(typeof label != "string")
			throw Error("label should be a string")		
		if(!(label in activeElements))
			throw Error("not exist that element inside active Elements")
		
		delete activeElements[label];
		elementIndex = Object.keys(activeElements);
		
		console.log("desactivated element " + label)

		return this; 
	}
	
	// recibe la info del evento la procesa y llama a los métodos de los elementos activos que esten relacionados con ese evento
	// el formato de la info tiene que ser un objeto de la siguente manera:

	// {"type": , "arguments":}



	publish = function(name, arg){

		// console.log("Mediator ha recibido el evento " + name + "con los siguientes parámetros: ")
		// console.log(arg);

		if(!channels[name]) return false;

		for(var i =0; i<channels[name].length;i++)

			channels[name][i].callback.apply(channels[name][i].context, arg);

		return this; // Para poder concatenar los metodos
	}


	subscribe = function(name, call){

		
		var nameBrod = undefined,
			typeBrod = undefined;
		// Casos especiales de broadcast

		// Una callback para varios eventos
		if(name.slice(0,name.indexOf(".")) == "all"){
		
			typeBrod = name.slice(name.indexOf(".") + 1);

			for(var i=0 ; i < elementIndex.length ; i++){

				nameBrod = elementIndex[i] + "." +typeBrod;
				
				if(!channels[nameBrod]) channels[nameBrod] = new Array();

				channels[nameBrod].push({context: this, callback: call})

			}

			return this;
		}


		if(call === "all"){
			typeBrod = name.slice(name.indexOf(".") + 1);

			for(var i = 0; i < elementIndex.length; i++){
				//nameBrod = elementIndex[i] + "." + typeBrod;
				
				if(!channels[name]) channels[name] = new Array();
				
				if(activeElements[elementIndex[i]][typeBrod])
					channels[name].push({context: this, callback: activeElements[elementIndex[i]][typeBrod]})				
			}

			return this;
		}

		// Un evento para 
		if(!channels[name]) channels[name] = new Array();

		if(Array.isArray(call)){

			for(var i = 0; i< call.length; i++){

				if(typeof(call[i])!= "function")
					throw Error("secod argument must be a function or an array of functions");
				
				channels[name].push({context: this, callback: call[i]}) 
			}



			return this;

		}


		if(typeof(call)!= "function" )
			throw Error("secod argument must be a function or an array of functions");


		

		channels[name].push({context: this, callback: call});
	}


	getActiveElements = function(){
		return activeElements
	}

	//----------------------------------------------------------------------


	return {

		activeElements: active,
		desactiveElement: desactiveElement,
		publish: publish,
		subscribe: subscribe,
		getActiveElements:getActiveElements
	};
}

