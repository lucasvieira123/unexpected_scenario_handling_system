import re
import os


class ClassBuilder:
    def __init__(self, class_file, expected_scenario_json, variables_config_json):
        self.class_file = class_file
        self.expected_scenario_json = expected_scenario_json
        self.variables_config_json = variables_config_json
        self.class_name = "DynamicClass"
        self.vars_config_dict = {}

    def build_dinamic_class(self):
        self.create_file()
        self.create_class_signature_and_constructor_and_global_vars()
        self.create_method_dynamically()
        self.create_update_variables()

    def create_file(self):
        
        # Verifica se o arquivo existe
        if os.path.exists(self.class_file):
            # Exclui o arquivo existente
            os.remove(self.class_file)

        # Cria um novo arquivo vazio
        with open(self.class_file, 'w') as file:
            pass

    def create_class_signature_and_constructor_and_global_vars(self):
        
        lines = []

        lines.append(f"class {self.class_name}:")
        lines.append("    def __init__(self):")

        for item in self.variables_config_json:
            var_name = item['name']
            var_type = item['type']
            min_value = item.get('min_value')
            max_value = item.get('max_value')

            lines.append(f"        self.{var_name} = None  # {var_type} Range: [{min_value}, {max_value}]")

            self.vars_config_dict[var_name] = {
                "type": var_type,
                "min_value": min_value,
                "max_value": max_value
            }

            lines.append(f"        self.action = None")

        # Juntando todas as linhas em uma única string
        class_code = "\n".join(lines)

        with open(self.class_file, 'w') as file:
            file.write(class_code)

    def add_dot_self(self, string):
        # Adiciona self. antes de cada variável
        for var_name in self.vars_config_dict.keys():
            string = re.sub(r'\b' + var_name + r'\b', f'self.{var_name}', string)

        return string

    def create_method_dynamically(self):


        with open(self.class_file, "r") as file:
            existing_code = file.read()

        new_methods_code = ""

        for scenario in self.expected_scenario_json:

                for key, scenario_content in scenario.items():
                        if key != "_extra":
                            #criar estados initial, transition e final para um cenário

                            BDD_scenario=scenario_content
                            scenario_name = key

                            given = BDD_scenario.get("Given")
                            when = BDD_scenario.get("When")
                            do = BDD_scenario.get("Do")
                            then = BDD_scenario.get("Then")

                            given=self.add_dot_self(given)
                            when=self.add_dot_self(when)
                            then=self.add_dot_self(then)

                            pattern = r'(?<![!<>])=(?![=<>])'
                            # Substituir '=' por '=='
                            when = re.sub(pattern, '==', when)

                            # Regex para encontrar AND e OR como palavras isoladas
                            pattern_and = r'\bAND\b'
                            pattern_or = r'\bOR\b'

                            # Substituir AND por and
                            when = re.sub(pattern_and, 'and', when)

                            # Substituir OR por or
                            when = re.sub(pattern_or, 'or', when)

                            body = ""
                            methed_name = f"{scenario_name.lower()}__when"

                            if when == "*":
                                body = "return True"
                            else: body = f"if {when}: return True\n       else: return False"
                            decorator = "    @property\n"
                            method_def = f"    def {methed_name}(self):\n       {body}\n\n"
                            new_methods_code += decorator + method_def
                            
        # Append the new methods before the end of the file
        updated_code = existing_code.rstrip() + "\n\n" + new_methods_code

        with open(self.class_file, "w") as file:
            file.write(updated_code)

    def create_update_variables(self):
        lines = []
        for item in self.vars_config_dict.keys():
            var_name = item
            lines.append(f"        self.{var_name} = new_data[\"{var_name}\"]")
        

        lines.append(f"        self.action = new_data[\"action\"]")
        # Juntando todas as linhas em uma única string
        method_code = "\n".join(lines)

        with open(self.class_file, "a") as file:
            file.write(f"    def create_update_variables(self, new_data):\n{method_code}\n")