from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, validators
from wtforms.validators import DataRequired, email_validator, EqualTo, ValidationError
from app.models import Users
import re


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Please Log In')



class RegistrationForm(FlaskForm):
    username = StringField('Email Address', validators=[DataRequired()])
    mobile = StringField('Mobile', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


    def validate_username(form, field):
        # pass the regular expression 
        # and the string in search() method 
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if(re.search(regex,field.data)):  
            user = Users.query.filter_by(username=field.data).first()
            if user is not None:
                note = 'This email address is already in use.'
                field.errors.append(note)
                note = 'Please use a different email address.'
                field.errors.append(note)
                #raise ValidationError(email.errors)
        else:  
            raise ValidationError('Email address is not valid')


    def validate_password(form, field):
      
        SpecialSym =['$', '!', '#', '%', '_', '~'] 
        val = True
        message=""
      
        if len(field.data) < 8: 
            note = 'Password length should be at least 8 characters.'
            message = message + note
            field.errors.append(note)
            val = False
                    
        if not any(char.isdigit() for char in field.data): 
            note = 'Password should have at least one numeral.'
            message = message + note
            field.errors.append(note)
            val = False
        
        if not any(char.isalpha() for char in field.data): 
            note = 'Password should have at least alphabetic letter.'
            message = message + note
            field.errors.append(note)
            val = False
          
        # if not any(char.isupper() for char in field.data): 
        #     note = 'Password should have at least one uppercase letter.'
        #     message = message + note
        #     field.errors.append(note)
        #     val = False
          
        # if not any(char.islower() for char in field.data): 
        #     note = 'Password should have at least one lowercase letter.'
        #     message = message + note
        #     field.errors.append(note)
        #     val = False
          
        # if not any(char in SpecialSym for char in field.data): 
        #     note = 'Password should have at least one of the symbols ($ ! # % _~).'
        #     message = message + note
        #     field.errors.append(note)
        #     val = False

    
        #if not val:
        #    raise ValidationError(field.errors)
            


