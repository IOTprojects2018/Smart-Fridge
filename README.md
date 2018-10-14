# Smart-Fridge

Visit http://smartfridge.ml/ to watch some videos about the project.

![alt text](https://github.com/IOTprojects2018/Smart-Fridge/blob/master/usecase.PNG)

- SHORT DESCRIPTIONS OF THE ACTORS
  - The central actor of the system is the **Web Service Catalog**. All the other actor in order to do something need to obtain information of the other actors in the system asking to Web Service Catalog. In this way, the Web Service Catalog must be started as first actor, the other actors can be started even in random order. All the actors send their own information to Web Service Catalog while they are working.

  Let's look at the other actors:

  - On the Raspberry Pi, 3 actors are working:
  1) **Raspberry Web** Service lets to  set up your personal system by connecting to Raspberry Web Service local website
  2) **Raspberry Publisher** is a multithread  publisher that lets to publish on diffent topics the data retrieved from sensors.
  3) **ImageClient** is a client which uploads a photo taken inside the fridge on Image Web Service every 20 seconds 

  - The Control Strategies are composed by 5 microservices:
  1) **Temperature Control** works as MQTT subscriber receiving temperature data from  Raspberry Publisher topics and if it is over a certain threshold, through RefrigeratorAllarm_bot can allarm the owner of the fridge. It also works as publisher publishing again the data in order to make them approchable to ThingSpeak Adaptor.
  2) **Humidity Control** works as MQTT subscriber receiving humidity data from  Raspberry Publisher topics. . It also works as publisher publishing again the data in order to make them approchable to ThingSpeak Adaptor.
  3) **Motion Control** works as MQTT subscriber receiving motion data from  Raspberry Publisher topics. It also works as publisher publishing again the data in order to make them approchable to ThingSpeak Adaptor.
  4) **Barcode&Weight Control** works as MQTT subscriber receiving Barcodes and weight data from  Raspberry Publisher topics. It is able to understand if a received barcode belongs to a new added product or to an old removed product by looking at the current weight value. It also works as publisher publishing again the barcode adding the key in the message that says if a product was inserted or removed in the fridge.
  5) **Image Web Service** works as a web server for images inside all the fridges

  - The Adaptors:
  1) **Products Adaptor** works as MQTT subscriber receiveing data from Barcode&Weight Control topics. Working also as REST client, It uses the data received to make a GET request to Barcode2Product Web Service obtaining the corrispondent product in order to then make a PUT request to Products Web Service updating the current user's product list.
  2) **ThingSpeak Adaptor** works as MQTT subscriber receiveing data from Temperature, Humidity, Motion and Weights Control topics. Working also as REST client, It uses the data received to make some GET requests to ThingSpeak updating the current user's proper channel field.

  - Other Web Services:
  1) **Barcode2Product Web Service** has as main function the capability to return a product name with its features after have received a GET request containing a barcode which is in its database.
  2) **Products Web Service** it's used has a server for the product lists of the users. It is possibile to add or remove a product by PUT requests.  

  - The Bots:
  1) **Refrigetator_bot** is able to get and send to user on telegram, data from thingspeak before asking to WebService Catalog the proper user's channel and read key of Thingspeak. It can also get from Products Web Service the current user's product list .
  It can also send images of the internal of the fridge obtaining them from Image Web Service and sending to user on telegram exploting **ColdImage_bot**
  2) **RefrigeratorAllarm_bot** is used by Temperature_Control to allarm the user about the temperature.


--
