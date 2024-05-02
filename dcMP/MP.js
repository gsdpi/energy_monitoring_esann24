function MP(iden,dtCb,softGrouping){
/*
Class which creates a crossfilter-based datacube and provides the user with public methods
to reproduce basic OLAP datacube operations such as aggregation, group, drill down/up and filter. 
*/

  // Private atributes
  var id,
      dtCb,
      encodings,
      activeEnc,
      pos,
      atts,
      activeAtts,
      excludedAtt,
      Q,
      softG;

  var defaultEnc = 0.1;
  var thrhld =0.002

  var dispatcher = d3.dispatch('exports')
  init(iden,dtCb,softGrouping);

  // Private methods
  // function softmax(x)
  // {
  //   var sen = 10
  //   x = [defaultEnc].concat(x)
  //   var sum = x.reduce((s,x) => s + Math.exp(x*sen),0)
  //   //console.log(sum)
  //   return x.map(d => Math.exp(d*sen)/sum)
  // }



 function softmax(x)
  {
    var sen = 10

    // aplicamos coeficiente de sensibilidad de morphing (sen = 10)
    x = [defaultEnc].concat(x)
    x = x.map(x => x*sen)  

    // calculamos función softmax para obtener los pesos "a"
    var ex      = x.map(x => Math.exp(x))       // exponentes de z_i
    var suma_ex = ex.reduce( (x,v) => x + v)    // suma de los exponentes de z_i 
    var a       = ex.map( x => x/suma_ex)       // exponentes de z_i / suma de exponentes de z_i

    // No sé por qué razón así parece ir mucho más rápido. 
    a = a.map(x => Math.round((x + Number.EPSILON) * 1000) / 1000)
    return a
  }


  function morphing(E,lambda)
    {
      // morphing(E,lambda) - morphing entre 2D arrays de posiciones

      //      E: array de M arrays (N,2) con las posiciones 2D de los encodings base
      // lambda: array de M pesos, que deberían sumar 1


      // recorremos las N posiciones de cada array
      lambda = lambda.slice(1)
      return E[0].map( (d,i) =>
      {
        // para cada posición, hacemos la suma ponderada 
        // de las posiciones de los encodings base        
        s = [0,0]
        for (j in E)
          {
            s[0] += lambda[j]*E[j][i][0] 
            s[1] += lambda[j]*E[j][i][1] 
          }
        return s
      })
    }


  function genEncBase(){
    //console.log("Generating encodings")
    // Generación de un ID para la creación de grupos unívocos para cada instancia de MP
    //var measures = Object.keys(activeEnc).concat(Object.keys(activeAtts))
    var measures = Object.keys(activeAtts)

    // Aquí hay que comprobar antes de crear el grupo la resolución. Si se indica la resolución se crea el grupo con esa resolución. En caso contrario, si limita el 
    // número de bins a 50. Utilizar el código de ihist para implementar eso. 

    dtCb.group("MP_"+id,Object.keys(activeEnc),undefined,measures)

    eventInfo = {"type":"updateMPGroups","arguments":[{"Param1":"Soy un parametro ejemplo"}]};
    dispatcher.call("exports",this,eventInfo); 
  }

  function updatePoints(){
    //console.log("Updating pos")
    
    var E = []
    Object.keys(activeEnc).forEach( (key,i,a) => E[i] = dtCb.group('MP_'+id)['Values'].map(d=>encodings[key](d.key[i])))
    var lambdas =  Object.values(activeEnc)

    excludedEnc.forEach(d=>lambdas[Object.keys(activeEnc).lastIndexOf(d)]=-1000)

    var L = softmax(Object.values(lambdas))
    pos   = morphing(E,L)

    eventInfo = {"type":"updatePoints","arguments":[]};
    dispatcher.call("exports",this,eventInfo); 
    
  }

  function init(iden,dtCb,softGrouping){
    id        =iden;
    dtCb      = dtCb;
    encodings = new Object();
    activeEnc = new Object();
    activeAtts = new Object();
    excludedEnc = [];
    softG = softGrouping
    Q = new Object();

    //return console.log("Creado objeto morphing projection " + iden)
  }

  // This function returns a lookup table with base point positions from the att info returned from datacube object.
  // Basic encodings are supported: circular, horizontal, vertical, vertical.
  function generatorEnc(type, attInfo, lookup){
     
     switch(type){

       case "vertical":
         return d => [ 0,(10*d/attInfo['max']) -5];
       case "horizontal":
         return d =>[(10*d/attInfo['max']) -5,0];
       case "circular":
          return d => [5*Math.sin(2*Math.PI*d/(attInfo['max']+1)),5*Math.cos(2*Math.PI*d/(attInfo['max']+1))];
       case "custom":
           return function(d){ var lut = lookup;
                               return [lut[d]['x'],lut[d]['y']]; 
                              };
     }


  }

  // Dummy exports needed to create the clousure
  function exports(){
    
  }
  
  // Public methods
  exports.getID = function(){
    return id
  }



  exports.changeEnc = function(n,v){
    // It creates or removes the groups associated to the active encodings. 
    // It also update the position (x,y) and the rest of the attributes attached to the points.
    // It returns "true" if there is a change in the active encodings and 'false' if only update the positions and attributes
    // Turn on a new encoding 
    

    Q[n] = v
    var isChange = false;
    var L = Object.values(Q)
    if(softG){
      L = softmax(Object.values(Q));
      L = L.slice(1) // removing the initial encodings
    }

    names = Object.keys(Q);
    L.forEach(function(v,i){

        n = names[i]
        if(v >=thrhld && !(n in activeEnc) && Q[n]>0){
              activeEnc[n]=Q[n]
              isChange = true;
          }
          // Turn off the encoding
          else if((v<thrhld || Q[n]<=0) && (n in activeEnc) ){
            delete activeEnc[n]
            isChange = true;
          }
          else if(v<thrhld && !(n in activeEnc)){
            
          }
          // Only update the position
          else{
            if(n in activeEnc)
              activeEnc[n] = Q[n]
          }
      })
    if(isChange)
       genEncBase()


    updatePoints()

    return isChange

    
  }



  exports.addEncoding = function(att,lookup,type){
    
    if(! att in Object.keys(dtCb.getDataInfo()))
      throw new Error(" Att not included in the created datacube. MP.js class error");    


    if(type == "custom")
      encodings[att] = generatorEnc(type,dtCb.getDataInfo()[att],lookup);
    else
      encodings[att] = generatorEnc(type,dtCb.getDataInfo()[att],undefined) 
      
    
    return -1;
  }

  exports.changeTypeEnc = function(att,newType){

    if(!att in Object.keys(encodings))
      throw new Error(" Att not included in the available MP attributes. MP.js class error");          

    encodings[att] = generatorEnc(newType,dtCb.getDataInfo()[att],undefined) 
    updatePoints()
  } 

  exports.removeEncoding = function(att){
    if(att in encodings)
      delete encodings[att]
    return -1
  }

  exports.addAtt = function(att){
    activeAtts[att] = undefined
    return -1;
  }

  exports.removeAtt = function(att){
    if(att in activeAtts)
      delete activeAtts[att]
    return -1;
  }

  exports.getActiveEnc= function(){
    return activeEnc;
  }

  exports.getPos = function(){
    return pos;

  }
  exports.getAtt = function(att,agg){
    if(!(att in activeAtts)){
      throw Error(att+" attribute is not available");
    }

    if (dtCb.cellsIDs().lastIndexOf('MP_'+id) != -1){

      if (dtCb.group('MP_'+id)["Meta"]["Aggregations"].lastIndexOf(agg)==-1){
        throw Error(agg+" aggregation is not available");
      }
      //console.log(dtCb.group('MP_'+id)["Values"][0])
      if(agg === "count"){
        return dtCb.group('MP_'+id)["Values"].map(d =>d.value[agg])
      }
      else{
        return dtCb.group('MP_'+id)["Values"].map(d =>d.value[agg+att])
      }
    
    }
    
    return undefined
    
  }
  exports.getAttIDs = function(){

    return activeAtts;
  }
  
  exports.excludeEnc = function(att){
    excludedEnc.push(att);
    return -1;
  }

  exports.getAtts = function(){

    Object.keys(activeAtts).forEach(function(v,i){
                      activeAtts[v]=dtCb.group('MP_'+id)["Values"].map(d =>d.value['avg'+v])
      })
    return activeAtts
  }

  exports.getGroup = function(){
    return dtCb.group('MP_'+id)
  }

  exports.update = function(source){

    updatePoints()

    return -1;
  }

  exports.updateEvent = function(source){

    eventInfo = {"type":"updatePoints","arguments":[]};
    dispatcher.call("exports",this,eventInfo); 

    return -1;
  }

  exports.setThrshld= function(v){
    thrhld = v
    return -1;
  }


  exports.on = function(){

    var value = dispatcher.on.apply(dispatcher,arguments);
    return value === dispatcher ? exports : value;

  }


  return exports;
}

