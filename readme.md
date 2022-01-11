Super Cool Comics Project:
Sprint one link:

https://lit-tundra-86808.herokuapp.com/


Sprint two link (most recent):

https://domino-pizza-rocketlauncher.herokuapp.com/

For our class project, we created a web applicaton, that allows user to use basic functionality such as, creating an account, logging into their account, and adding their favorite characters and comics underneath their username.

Our web application is a Marvel-Universe themed website. We implemented the Marvel API that allows us to go through their databases of information that stores comic books and characters. With the API, when the user searches for a specific comic book and/or character, it will populate the top 10 results of their search. With the populates results of the users' search, the user have the ability to click on the title of the comic and/or character and it will redirect the user to another page. For right now, the page has a Favorite button with no information displayed. Next sprint we'll polish it to have various information relevant to the user based on the comic/character. In addition, the users have the ability to take a quiz on their knowledge of the Marvel Universe.

We have implemented our own crypto encryption to keep our users' password/account protected.

We created our web application with HTML, CSS, JavaScript, and Python.

NOTE 12/3/2021:
A change was made to the Marvel Api so that if we made calls in quick succession, then the app breaks. How we had it before was we made two calls for every search. One to make sure the call was valid, and the other to actually return the data. This was fixed by moving the error checking to the api.app side of things, but the other issue was the profile page using a call for every thing in the user's favorited list. To get around this, we made a pipeline that didn't push data through immediately. Instead, it has it so an API call is made every .2 seconds so data is actually returned. This wouldn't be an issue if it wasn't for the other bug with the api itself, which is that when you put in the id of an individual character or comic, it would sometimes return the id back to the user instead of the data in the json. To get around this, we performed a check to see if the data being passed back was an int, and if it was, then it would run the same function again. This on top of the app making an api call every .2 seconds would mean the profile page takes a lot longer to load up than on the presentation. This was our solution to the changes made to the API.

FORMATTING NOTES: 
#App.py:

    inconsistent-return-statements:
    changing /any/ of the returns we have set up breaks the app

    no-else-return:
    tried changing these to the proper format of 
    if():
     return()
    return()
    but it broke the app
        
     no-member:
     raised for every reference to the SQLAlchemy DB due to pylints static nature
        
     no-self-use:
     raised on lines 56 & 64. db.model needs these args
        
     invalid-name:
     raised on lines 289,448,454. I tried playing with changing these lines and everything broke.
        
     invalid-envvar-default:
     disabled due to pylint not understanding the configuration of our app
        
#marvel_api.py        
        
      global-statement:
      this is permissable per pep-8
        
    	unused-variable:
	    raised on line 126. we need this function call to establish parameters for the next method
    
    	consider-using-enumerate:
    	raised on lines 108,156,180. the indexing that enumerate does breaks functionality from our core search function
    
    	bare-except:
    	the actual named error raised here is somehow skipping this condition
