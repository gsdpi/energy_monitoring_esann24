function DataCube(_){
/*
Class which creates a crossfilter-based datacube and provides the user with public methods
to reproduce basic OLAP datacube operations such as aggregation, group, drill down/up and filter. 
*/

  // PRIVATE ATTRIBUTES
  var data,
      cells,
      dimensions,
      reducter,
      dataAttributes,
      ObjCrossfilter,
      eventInfo,
      dataInfo;


  var dispatcher = d3.dispatch('exports'); 

  init(_);
  ///////////////////////////////////////////////////////////////////////////////////////////
  //  PRIVATE METHODS

  // Max Min custom fuctions are needed beacuse built-in functions crash 
  // because they exceed the maximum call stack size when the array's length is greater than 10^5. 
  function getMax(arr) {
      let len = arr.length;
      let max = -Infinity;

      while (len--) {
          max = arr[len] > max ? arr[len] : max;
      }
      return max;
  }


  function getMin(arr) {
      let len = arr.length;
      let min = Infinity;

      while (len--) {
          min = arr[len] < min ? arr[len] : min;
      }
      return min;
  }


  function computeDataInfo(){
    var attNames = Object.keys(data[0]);
    var datInfo  = {};

    
    attNames.forEach(function(d){
                                  
                                  attValues = data.map(d_v=>d_v[d])
                                  datInfo[d] = {}
                                  datInfo[d]['max'] = getMax(attValues) 
                                  datInfo[d]['min'] = getMin(attValues) 
                                  datInfo[d]['n_unique'] = [... new Set(attValues)].length
                                  return -1;
                                })

    return datInfo;

  }

  function groupFunction(_,t){
    /* 
      It creates the function to create the group

          t -->  datatype
          _ --> resolution 

    */
    switch(typeof _){
      // If resolution is a number, the resulting group has _ bins
      case "number":
        if(t == "number")
          return function(d){return Math.floor(d/_)*_};
        throw Error("Está intentando agrupar por una función de redondeo y el parámetro no es un número");
      // If resolucion is a string it is a categorical group
      case "string":
         console.log("Not implemented")
      // If resolution is a function, this function is considered the grouping function
      case "function":
        return _;
      
      //If an array is specified as the resolution of the group, each dimension of a multidimensional group is binned by the elements of this array
      case "object":
        if (! Array.isArray(_))
          throw new Error('Datacube error: resolution of a group must be a number, string, function or an array');
        return d => d.map(function(v,index){

                                            if(_[index] == undefined)
                                              return v;

                                            return Math.floor(v/_[index])*_[index];
                                          }
                          );
      //By default a group with the same bins than the unique opearation over the dimension will be created  
      case "undefined":
        return function(d){return d;}

    }
  }



  function dimensionFunction(dim,_,t){
    /* 
      It creates the function to create the dimension

          t -->  datatype
          _ --> resolution 
          dim --> the name of the dimension to be created

    */

    // If dim is an array a multidimensional dimension is created
    if(Array.isArray(dim)){


      return d => dim.map(x=>d[x])

    }
    else{
      // If dim is an datetime 
      if((t == "object") && (data[0][dim].setDate != undefined)){
          Console.log("The creation of datetime dimensions has not be implemented yet")      
      }
      else
        return function(d){return d[dim]};
    }
  }

function reducerFunction(mea, max_items){
   /*
    It generates the reducer that aggregates the group
      mea --> att used to aggregate all the items in each bin

      max_item --> maximum number of items used in the aggregation 
   */
   
    max_items = max_items || Infinity

    var reducerFunc = {}; // Nuevo objeto para alojar el custom reducer

    if(Array.isArray(mea)){
      
      reducerFunc.add = function(p,v,nf){
             p["count"] += 1;
             p["all_count"] = nf ? p["all_count"] + 1 : p["all_count"]

             if(p.count<=max_items){
                mea.map(function(key){
                  // With number computes the sum and avg aggregations

                  // To prevent errors with null number (NaN in python)
                  // To be careful with null values and string/categorical atts
                  v[key] = v[key] || 0
                  

                  if(typeof(v[key]) === "number"){
                    p['sum'+key] += v[key];
                    p['all_sum'+key] = nf ? p['all_sum'+key]+v[key]: p['all_sum'+key];
                    p['avg'+key]  = p['sum'+key]/p.count;
                    p['all_avg'+key]  = p['all_sum'+key]/p["all_count"];
                  


                  }
                           
                  // With string attributes it applies a unique operation on each bin
                  // Queda pendiente el los valores agregados all_
                  else{
                    // Real initialization for string atts
                    if(p.count==1 && !Array.isArray(p['sum'+key])){
                      p['uniques'+key] = {}
                      p['sum'+key] = []
                      p['avg'+key] = []
                    }
                    p["uniques"+key][v[key]] = v[key] in p["uniques"+key] ? p["uniques"+key][v[key]] + 1 : 1
                    p['sum'+key] = Object.keys(p["uniques"+key])
                    p['avg'+key] = Object.keys(p["uniques"+key])
                  }

                })
             }
             return p;
          }

         reducerFunc.remove =function(p,v,nf){
             
             p.count -=1;
             p["all_count"] = nf ? p["all_count"] - 1 : p["all_count"]

             if (p.count <=max_items){
               mea.map(function(key){

                if(typeof(v[key]) === "number"){
                  p['sum'+key] -= v[key];
                  p['all_sum'+key] = nf ?  p['all_sum'+key] - v[key] : p['all_sum'+key]

                  
                  p['avg'+key]  = p.count >0 ? p['sum'+key]/p.count : 0;                    
                  p['all_avg'+key] = p.all_count > 0 ? p['all_sum'+key]/p.all_count : 0

                }
                
                else{
                    p["uniques"+key][v[key]] = v[key] in p["uniques"+key] ? p["uniques"+key][v[key]] - 1 : 0
                    if(p["uniques"+key][v[key]] ==0)
                      delete p["uniques"+key][v[key]] 
                    p['sum'+key] = Object.keys(p["uniques"+key])
                    p['avg'+key] = Object.keys(p["uniques"+key])

                }

                })
             }

            return p;
         }

         reducerFunc.initial = function(){
           p={};
           p["count"] = 0
           p["all_count"] = 0
           mea.map(function(key){
              p['sum'+key] = 0;
              p['all_sum'+key] = 0;
              p['avg'+key] = 0;
              p['avg_sum'+key] = 0;
            })
           return p
         }
        
      

      reducer = function(g){g.reduce(reducerFunc.add,reducerFunc.remove,reducerFunc.initial)}

    }
    else{
      reducer = reductio().count(true).sum(d => d[mea]).avg(true)
    }

    return reducer;

  }


  function getDimensionName(dim){
    var dimName = new String();
    if(Array.isArray(dim)){
      for(var i=0;i<dim.length;i++)
        dimName = dimName + "/" + dim[i];
    }
    
    else{
        dimName = dim;
    }
    return dimName;
  }


  function cell(dim, reso,mea,max_items){
    var dtype = undefined,
        max_items = undefined,
        dimName,
        lims;

    if(!Array.isArray(dim))
      dtype = typeof data[0][dim]

    dimName = getDimensionName(dim)
    
    if (!(dimName in dimensions)){
      dimensions[dimName] = ObjCrossfilter.dimension(dimensionFunction(dim,reso,dtype));
    }
     // console.log("se crea una nueva dimension con el nombre:" + dimName);}

    this.dimension = dimensions[dimName];
    this.attr      = dim;
    this.resolution = undefined;
    this.group = dimensions[dimName].group(groupFunction(reso, dtype));
    this.measure = mea;
    this.filter = null;
    this.reducer = reducerFunction(mea,max_items)
    this.dimName = dimName

    this.reducer(this.group)


  }


  function removeCell(attr){
    cells[attr].group.dispose();
    cells[attr].dimension.dispose();
    cells[attr].dimension.filter(null);
    delete dimensions[cells[attr].dimName];
    return delete cells[attr];
  }

  ///////////////////////////////////////////////////////////////////////////////////////////
  // INITIALIZER
  function init(_){
    data = _;
    dataAttributes = Object.keys(data[0]);
    ObjCrossfilter= crossfilter(data);
    cells = new Object();
    dimensions = new Object();
    dataInfo  = computeDataInfo();
    //console.log("Creado un crossfilter con " + String(ObjCrossfilter.size())+" registros")
    return -1
  }


  // Dummy exports needed to create the clousure
  function exports(){
    
  }
  
  ///////////////////////////////////////////////////////////////////////////////////////////
  // PUBLIC METHODS


  exports.getData = function(){
    return data
  }


 
  exports.group = function(attr, dim, reso, mea){
  /*
    It creates the group from a previously defined dimension

        attr --> Identified of the resulting cell
        dim  --> Dimension on which the grouping operation will be applied
        reso --> Resolution of the grouping operation or the grouping function
        mea  --> Attribute or attributes used in the aggregation operation
  */ 

    if (Array(1,3,4).indexOf(arguments.length) == -1) {

      throw new Error("function called with " + arguments.length +
      " arguments, but it expects 4 arguments.");

      return -1;
    }
    argLength = arguments.length

    if ( Array.isArray(dim) && !((reso == null) || (reso == undefined) || Array.isArray(reso))){

      throw new Error("function called with wrong arguments");
      return -1;
    }

    // Getter option
    if (argLength==1){

      //console.log("Solicitado los elementos de un grupo");
      if (attr in cells) return {"Meta": {"Attribute": cells[attr].attr, 
                                          "ID":      attr,
                                          "Resolution":cells[attr].resolution,
                                          "Aggregations": ["count","sum","avg"],
                                          "Measure": cells[attr].measure,
                                          "Measures": dataAttributes},

                                 "Values":cells[attr].group.all()};
      return -1;
    } 

    // If measure is not defined, it is replaced by dim
    mea = mea || dim; 

    if(attr in cells){

      removeCell(attr);
      cells[attr] = new cell(dim,reso,mea);
      eventInfo = {"type":"update","arguments":[]};
      dispatcher.call("exports",this,eventInfo);   
      //console.log("nuevo atributo " + attr  + " actualizado en la dimension " + dim );
      return -1;
    }
    else{
      cells[attr] = new cell(dim,reso,mea);
      //console.log("nuevo atributo " + attr  + " generado a partir de la dimensión " + dim);
      return -1;
    }


  }


  exports.filter = function(cellID, filter){

    /*  
      It filters the dimension associated to the cellID indicated in dim 

          cellID --> identifier of the cell
          filer  --> It must be a range. Filter exact has not been implemented yet
    */
    if (Array(1,2).indexOf(arguments.length)==-1){
      throw new Error("function  called with wrong number of arguments");
      return -1;  
    }

    if ( (arguments.length == 1) && (filter == undefined) ) return cells[cellID].filter; 

    cells[cellID].dimension.filter(filter);
    cells[cellID].filter = filter;
    eventInfo = {"type":"update","arguments":[]};
    dispatcher.call("exports",this,eventInfo); 
    //console.log("Filtrado");
    return -1;
  }


  exports.measure = function(dim, measure){

    if (Array(1,2).indexOf(arguments.length)==-1){
      throw new Error("function  called with wrong number of arguments");
      return -1;  
    }

    if (!(dim in cells))
    {
      throw new Error("Group name is not within available groups in datacube")
      return  -1;
    }

    // Get
    if ( (arguments.length == 1) && (measure == undefined) )
         return cells[dim].measure; 
    
    // Set
    cells[dim].reducer = reducerFunction(measure, undefined);
    cells[dim].measure = measure;
    cells[dim].reducer(cells[dim].group)
    // Update event
    eventInfo = {"type":"update","arguments":[]};
    dispatcher.call("exports",this,eventInfo);  
  }



  exports.info = function(attr){
    if(cells[attr] != undefined) return cells[attr];
    throw new Error("Attribute selected are not available");
    
  }



  exports.cellsIDs = function(){
    return Object.keys(cells);
  }

  exports.cells = function(){
    return cells;
  }

  exports.availableAtt = function(){
    return dataAttributes
  }

  exports.update = function(){

    eventInfo = {"type":"update","arguments":[]};
    dispatcher.call("exports",this,eventInfo); 
    return -1
  }

  exports.getDataInfo = function(){

    return dataInfo
  }

  exports.getDimensions = function(){

    return dimensions
  }

  exports.on = function(){
        var value = dispatcher.on.apply(dispatcher,arguments);
        return value === dispatcher ? exports : value;
    } 
  return exports;
}