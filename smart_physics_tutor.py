from flask import Flask, render_template, request, jsonify
import owlready2
import re
import os
import numpy as np

class PhysicsFormulaValidator:
    def __init__(self, ontology_path):
        """
        Initialize the validator with the OWL ontology file
        """
        try:
            # Load the ontology
            self.ontology = owlready2.get_ontology(f"file://{ontology_path}").load()
            
            # Extract validation rules for different formulas
            self.validators = {}
            self.extract_all_validation_rules()
        except Exception as e:
            print(f"Ontology Loading Error: {str(e)}")
            raise
        
    def extract_all_validation_rules(self):
        """
        Extract comprehensive validation rules for all physics formulas in the ontology
        """
        try:
            # Formula validators to extract
            formula_validators = [
                'NewtonSecondLawValidator', 
                'KineticEnergyValidator', 
                'OhmsLawValidator', 
                'IdealGasLawValidator'
            ]
            
            for validator_name in formula_validators:
                validator = list(self.ontology.search(iri=f"*{validator_name}"))[0]
                
                self.validators[validator_name] = {
                    'formula_pattern': self.get_property_value(validator, 'hasFormulaPattern'),
                    'validation_rules': self.get_property_values(validator, 'hasValidationRule'),
                    'unit_constraints': self.get_property_values(validator, 'hasUnitConstraint'),
                    'value_constraints': self.get_property_values(validator, 'hasValueConstraint')
                }
        except Exception as e:
            print(f"Rule Extraction Error: {str(e)}")
            raise
        
    def get_property_value(self, instance, property_name):
        """
        Get a single property value from the ontology
        """
        try:
            prop = getattr(instance, property_name, [])
            return prop[0] if prop else None
        except Exception as e:
            print(f"Property Retrieval Warning: Could not retrieve {property_name}: {str(e)}")
            return None
        
    def get_property_values(self, instance, property_name):
        """
        Get multiple property values from the ontology
        """
        try:
            return getattr(instance, property_name, [])
        except Exception as e:
            print(f"Property Retrieval Warning: Could not retrieve {property_name}: {str(e)}")
            return []
        
    def validate_formula(self, formula_type, formula):
        """
        Validate different physics formulas using ontology rules
        """
        # Validate against ontology-defined formula pattern
        validator_info = self.validators.get(formula_type)
        if not validator_info:
            return False, "Unsupported formula type"
        
        # Check formula pattern
        formula_pattern = validator_info['formula_pattern']
        if not re.match(formula_pattern, formula.replace(' ', '')):
            return False, f"Formula must match pattern: {formula_pattern}"
        
        # Validate variables
        try:
            calculation_result, parsed_values = self.parse_and_validate_values(formula_type, formula)
            
            # Prepare validation messages
            validation_messages = (
                validator_info.get('validation_rules', []) + 
                validator_info.get('unit_constraints', []) +
                validator_info.get('value_constraints', [])
            )
            
            result_message = f"Calculation Successful! Result = {calculation_result:.2f}\n"
            result_message += "\n".join(validation_messages)
            
            return True, result_message
        
        except ValueError as ve:
            return False, str(ve)
        except Exception as e:
            return False, f"Validation Error: {str(e)}"
    
    def parse_and_validate_values(self, formula_type, formula):
        """
        Parse and validate formula values dynamically based on ontology constraints
        """
        # Remove spaces for consistent parsing
        formula = formula.replace(' ', '')
        
        # Mapping of validation logic for each formula type
        validation_strategies = {
            'NewtonSecondLawValidator': self._validate_newton_second_law,
            'KineticEnergyValidator': self._validate_kinetic_energy,
            'OhmsLawValidator': self._validate_ohms_law,
            'IdealGasLawValidator': self._validate_ideal_gas_law
        }
        
        # Get the appropriate validation strategy
        strategy = validation_strategies.get(formula_type)
        if not strategy:
            raise ValueError("No validation strategy found")
        
        return strategy(formula)
    
    def _validate_newton_second_law(self, formula):
        """
        Validate Newton's Second Law formula with ontology constraints
        """
        # Regex to extract mass and acceleration
        match = re.match(r'F=(\d+(\.\d+)?)\*(\d+(\.\d+)?)', formula)
        
        if not match:
            raise ValueError("Invalid Newton's Second Law formula")
        
        mass = float(match.group(1))
        acceleration = float(match.group(3))
        
        # Apply value constraints from ontology
        validator_info = self.validators.get('NewtonSecondLawValidator', {})
        value_constraints = validator_info.get('value_constraints', [])
        
        # Check mass constraint
        if 'Mass (m) must be a positive number greater than 0' in value_constraints:
            if mass <= 0:
                raise ValueError("Mass must be a positive number greater than 0")
        
        # Calculate force
        force = mass * acceleration
        return force, {'mass': mass, 'acceleration': acceleration}
    
    def _validate_kinetic_energy(self, formula):
        """
        Validate Kinetic Energy formula with ontology constraints
        """
        # Regex to extract mass and velocity
        match = re.match(r'KE=0.5\*(\d+(\.\d+)?)\*(\d+(\.\d+)?)\^2', formula)
        
        if not match:
            raise ValueError("Invalid Kinetic Energy formula")
        
        mass = float(match.group(1))
        velocity = float(match.group(3))
        
        # Apply value constraints from ontology
        validator_info = self.validators.get('KineticEnergyValidator', {})
        value_constraints = validator_info.get('value_constraints', [])
        
        # Check mass and velocity constraints
        if 'Mass (m) must be a positive number greater than 0' in value_constraints:
            if mass <= 0:
                raise ValueError("Mass must be a positive number greater than 0")
        
        if 'Velocity (v) must be non-negative' in value_constraints:
            if velocity < 0:
                raise ValueError("Velocity must be non-negative")
        
        # Calculate kinetic energy
        kinetic_energy = 0.5 * mass * (velocity ** 2)
        return kinetic_energy, {'mass': mass, 'velocity': velocity}
    
    def _validate_ohms_law(self, formula):
        """
        Validate Ohm's Law formula with ontology constraints
        """
        # Regex to extract current and resistance
        match = re.match(r'V=(\d+(\.\d+)?)\*(\d+(\.\d+)?)', formula)
        
        if not match:
            raise ValueError("Invalid Ohm's Law formula")
        
        current = float(match.group(1))
        resistance = float(match.group(3))
        
        # Apply value constraints from ontology
        validator_info = self.validators.get('OhmsLawValidator', {})
        value_constraints = validator_info.get('value_constraints', [])
        
        # Check current and resistance constraints
        if 'Current (I) must be non-negative' in value_constraints:
            if current < 0:
                raise ValueError("Current must be non-negative")
        
        if 'Resistance (R) must be a positive number greater than 0' in value_constraints:
            if resistance <= 0:
                raise ValueError("Resistance must be a positive number greater than 0")
        
        # Calculate voltage
        voltage = current * resistance
        return voltage, {'current': current, 'resistance': resistance}
    
    def _validate_ideal_gas_law(self, formula):
        """
        Validate Ideal Gas Law formula with ontology constraints
        """
        # Regex to extract n, R, and T
        match = re.match(r'PV=(\d+(\.\d+)?)\*(\d+(\.\d+)?)\*(\d+(\.\d+)?)', formula)
        
        if not match:
            raise ValueError("Invalid Ideal Gas Law formula")
        
        n = float(match.group(1))   # moles
        R = float(match.group(3))   # gas constant
        T = float(match.group(5))   # temperature
        
        # Apply value constraints from ontology
        validator_info = self.validators.get('IdealGasLawValidator', {})
        value_constraints = validator_info.get('value_constraints', [])
        
        # Check value constraints
        if 'Number of Moles (n) must be a positive number greater than 0' in value_constraints:
            if n <= 0:
                raise ValueError("Number of moles must be a positive number greater than 0")
        
        if 'Gas Constant (R) must be a positive number greater than 0' in value_constraints:
            if R <= 0:
                raise ValueError("Gas constant must be a positive number greater than 0")
        
        if 'Temperature (T) must be non-negative (absolute temperature in Kelvin)' in value_constraints:
            if T < 0:
                raise ValueError("Temperature must be non-negative (absolute temperature in Kelvin)")
        
        # Calculate pressure * volume
        pv = n * R * T
        return pv, {'n': n, 'R': R, 'T': T}

# Flask Application
app = Flask(__name__)

# Global variable to store validator and mastery
class AppState:
    def __init__(self):
        # Hardcoded ontology path 
        ontology_path = os.path.join(os.path.dirname(__file__), 'smart_physics_tutor.owl')
        self.validator = PhysicsFormulaValidator(ontology_path)
        self.mastery_level = 0

app_state = AppState()

@app.route('/')
def index():
    """
    Render the main page
    """
    return render_template('index.html', 
                           mastery_level=app_state.mastery_level,
                           ontology_file=os.path.basename(os.path.join(os.path.dirname(__file__), 'smart_physics_tutor.owl')))

@app.route('/validate', methods=['POST'])
def validate_formula():
    """
    Validate the submitted formula
    """
    # Get formula and formula type from request
    formula = request.form.get('formula', '')
    formula_type = request.form.get('formula_type', 'NewtonSecondLawValidator')
    
    # Validate formula
    is_valid, message = app_state.validator.validate_formula(formula_type, formula)
    
    # Update mastery level
    if is_valid:
        app_state.mastery_level = min(app_state.mastery_level + 10, 100)
    else:
        app_state.mastery_level = max(app_state.mastery_level - 5, 0)
    
    # Return results
    return jsonify({
        'is_valid': is_valid,
        'message': message,
        'mastery_level': app_state.mastery_level
    })

if __name__ == '__main__':
    app.run(debug=True)