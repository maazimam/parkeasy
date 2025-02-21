# ParkEasy – The Smart Way to Park! 🚙  

🚀 **ParkEasy** is your go-to web app for finding and renting parking spots!  
No more circling the block—just book a spot, park, and go.  

*Brought to you by Team 3*

## Instructions

### 📌 1. Set Up the Virtual Environment
Before running the Django app, create and activate a virtual environment.

### For macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### For Windows (cmd)
```bash
python -m venv venv
venv\Scripts\activate
```

###  📦 2. Install Dependencies
Ensure all required dependencies are installed.

```bash
pip install -r requirements.txt
```

If new packages were installed, update `requirements.txt`:

```bash
pip freeze > requirements.txt
```

###  🔄 3. Apply Migrations
Run the following commands to set up the database:

```bash
python manage.py makemigrations
python manage.py migrate
```

###  🔑 4. Create a Superuser (Optional)
If you need access to the Django Admin panel:

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

### 🚀 5. Run the Development Server
Start the Django app:

```bash
python manage.py runserver
```

Access the app at http://127.0.0.1:8000/.

### 🛠️ 6. Adding New Dependencies
If you install any new libraries, make sure to update `requirements.txt`:

```bash
pip install <package-name>
pip freeze > requirements.txt
```

###  Code Organization 
- ```ParkEasy```: Main ParkEasy orchestration app. 
- ```accounts```: To manage accounts. 
- ```parkings_spot_listing```: For parking spot owners to list  and view their parking spots. 
- ```parking_spot_renting```: (not implemented yet), an app for users to look for parking spots.

## Resources
- Styling: https://getbootstrap.com/
- Django: https://www.djangoproject.com/start/