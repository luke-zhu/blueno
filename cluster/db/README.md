This directory contains the code for creating
the platform database.

Run `make create` to generate a fresh database.

## Creating a Team

As of 5/29/2019, additional users must be added manually. To
do so, follow the steps below:

1. Make a password and generate a hash of that password.
   In Python, you can do that with the method `werkzeug.security.generate_password_hash`
2. Connect to the database with `make psql`
3. Insert a new user by typing the following with your own email and password hash:
    ```
    INSERT INTO users (email, pwhash, created_at)
    VALUES (<YOUR_EMAIL>, <YOUR_PWHASH>, now())
    ```