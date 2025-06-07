# Authentication Setup for Pod GPT

This application now includes a user authentication and approval system. Users must register and be approved by an administrator before they can access the podcast generation features.

## Features

- **User Registration**: Users can sign up with name, email, and password
- **Admin Approval**: New users are pending approval by default
- **Login System**: Users can only login after being approved
- **Admin Panel**: Administrators can approve, reject, or revoke user access
- **Role-based Access**: Different permissions for regular users and administrators

## Initial Setup

### 1. Create an Admin User

Before users can be approved, you need to create an initial admin user:

```bash
# Activate your virtual environment
source venv/bin/activate

# Run the admin creation script
python create_admin.py
```

Follow the prompts to create your first admin user. This user will have:
- Full access to the application
- Admin privileges to approve other users
- Access to the admin panel

### 2. Start the Application

```bash
# With virtual environment activated
source venv/bin/activate
python app.py
```

The application will be available at `http://localhost:7000`

## User Workflow

### For Regular Users

1. **Sign Up**: Visit `/signup` to create an account
2. **Wait for Approval**: You'll see a message that your account is pending approval
3. **Login**: Once approved, you can login at `/login` and access the application

### For Administrators

1. **Login**: Login with your admin credentials
2. **Access Admin Panel**: Navigate to `/admin` or click "Admin" in the navigation
3. **Manage Users**: 
   - **Approve** pending users to grant access
   - **Reject** users to delete their accounts
   - **Revoke** access from approved users

## Admin Panel Features

The admin panel (`/admin`) provides:

- **Pending Approvals**: List of users waiting for approval
- **Approved Users**: List of all approved users with their roles
- **User Actions**: Approve, reject, or revoke access for users
- **Role Display**: Shows which users are admins vs regular users

## Database Schema

The authentication system adds the following fields to the User model:

- `id`: Primary key
- `email`: Unique email address
- `password`: Hashed password
- `name`: User's full name  
- `is_approved`: Boolean indicating if user can login
- `is_admin`: Boolean indicating admin privileges

## Security Features

- **Password Hashing**: All passwords are hashed using PBKDF2-SHA256
- **Session Management**: Flask-Login handles secure sessions
- **Admin Protection**: Admin routes require both login and admin privileges
- **CSRF Protection**: Forms include CSRF tokens for security

## Customization

### Making Users Auto-Approved

If you want to disable the approval system and auto-approve users:

1. Edit `auth.py` in the signup route
2. Change `is_approved=False` to `is_approved=True`
3. Remove the approval check from the login route

### Adding Email Notifications

You can extend the system to send email notifications:

- When users register (to admins)
- When users are approved/rejected (to users)
- Add email configuration to the Flask app

### Additional User Fields

The User model can be extended with additional fields like:
- `created_at`: Registration timestamp
- `last_login`: Last login timestamp
- `department`: User's department/organization
- `profile_picture`: User avatar

## Troubleshooting

### Database Issues

If you encounter database errors:

```bash
# Delete the existing database
rm db.sqlite

# Restart the application (it will recreate the database)
python app.py
```

### Permission Issues

If admin features aren't working:

1. Check that your user has `is_admin=True` in the database
2. Verify you're logged in as the admin user
3. Check the Flask application logs for errors

### Port Conflicts

If port 7000 is in use:

1. Edit `app.py` and change the port number
2. Or kill the process using the port: `lsof -ti:7000 | xargs kill` 