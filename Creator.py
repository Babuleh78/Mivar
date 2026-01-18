import pandas as pd
import re
from lxml import etree
import uuid

from XMLCreator import XMLCreator
from FormulaCreator import FormulaCreator
def main():
    OLD_EXCEL_FILE = "Phys8Class.xlsx" 

    FC = FormulaCreator()
    EXCEL_FILE = FC.process_excel_by_column(OLD_EXCEL_FILE)


    # Читаем все листы Excel
    df = pd.read_excel(EXCEL_FILE, sheet_name=None, dtype=str)
    
    # Словарь для хранения данных по классам
    classes_data = {}
    
    # Список для хранения всех формул с информацией о классе
    all_formulas_info = []
    
    # Множество всех переменных
    all_variables = set()

    # Обрабатываем каждый лист
    for sheet_name, sheet_data in df.items():
        # Предполагаем, что заголовки классов находятся в первой строке
        for col_idx, col_name in enumerate(sheet_data.columns):
            # Создаем запись для класса, если его еще нет
            if col_name not in classes_data:
                classes_data[col_name] = {
                    'variables': set(),
                    'formulas': [],
                    'xml_element': None,  # Будем хранить ссылку на XML-элемент класса
                    'rules_element': None  # Будем хранить ссылку на элемент правил
                }
            
            # Обрабатываем ячейки в этом столбце
            for cell_value in sheet_data[col_name]:
                if pd.notna(cell_value) and isinstance(cell_value, str):
                    cell_value = str(cell_value).strip()
                    
                    # Если это формула (содержит математические символы)
                    if any(sym in cell_value for sym in '=+-*/^()'):
                        # Ищем переменные в формуле
                        words = re.findall(r'\b[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\b', cell_value)
                        classes_data[col_name]['variables'].update(words)
                        all_variables.update(words)
                        
                        # Обрабатываем формулу, если она содержит '='
                        if '=' in cell_value:
                            left_part, right_part = cell_value.split('=', 1)
                            left_part = left_part.strip()
                            right_part = right_part.strip()
                            
                            # Добавляем левую часть как переменную
                            classes_data[col_name]['variables'].add(left_part)
                            all_variables.add(left_part)
                            
                            # Создаем шаблон формулы
                            template = create_formula_template(left_part, right_part)
                            
                            # Сохраняем информацию о формуле
                            formula_info = {
                                'class': col_name,
                                'original': cell_value,
                                'left': left_part,
                                'right': right_part,
                                'template': template,
                                'variables': words
                            }
                            
                            all_formulas_info.append(formula_info)
                            classes_data[col_name]['formulas'].append(formula_info)

    ################# Преобразование формул в relations_list
    relations_list = []
    template_counter = 1
    template_to_relation = {}  
    
    # Собираем все уникальные шаблоны
    all_templates = set()
    for formula_info in all_formulas_info:
        all_templates.add(formula_info['template'])
    
    # Создаем relation для каждого уникального шаблона
    for template in sorted(all_templates):
        if template.startswith("y="):
            formula_part = template[2:] 

            variables_in_template = re.findall(r'\b[a-z]\b', formula_part)
            
            input_vars = sorted(set(variables_in_template))
            
            in_obj_parts = []
            for var in input_vars:
                in_obj_parts.append(f"{var}:double")
            
            in_obj = ";".join(in_obj_parts) if in_obj_parts else " "
            
            # outObj: всегда 'y'
            out_obj = "y:double"
            
            relation_name = f"Rule_{template_counter}"
            relation = {
                'shortName': relation_name,
                'inObj': in_obj,
                'outObj': out_obj,
                'relationType': 'simple',
                'formula': template 
            }
            
            relations_list.append(relation)
            template_to_relation[template] = relation_name
            template_counter += 1

    ################# Создание XML
    
    creator = XMLCreator()

    model = etree.Element("model", 
                          id=f"{{{str(uuid.uuid4())}}}",
                          shortName=str(EXCEL_FILE),
                          formatXmlVersion="2.0",
                          description=str(EXCEL_FILE))
    model.text = "\n"

    main_class_elem, main_params, main_rules, main_constraints, classes_elem, relations_elem = creator.create_main_class(
        model, 
        str(EXCEL_FILE),
        relations_list=relations_list
    )

    
    # Создаем вложенные классы для каждого заголовка столбца
    for class_idx, class_name in enumerate(classes_data.keys(), 1):
        print(f"Создание класса {class_idx}: {class_name}")
        
        # Получаем переменные для этого класса
        class_variables = list(classes_data[class_name]['variables'])
        
        # Создаем вложенный класс и сохраняем его элементы
        nested_class, nested_params = creator.create_class(
            classes_elem, 
            class_name,
            is_nested=True,
            parameters_list=class_variables
        )
        
        # Сохраняем ссылку на XML-элемент класса
        classes_data[class_name]['xml_element'] = nested_class
        
        # Находим элемент правил для этого класса
        rules_element = nested_class.find("rules")
        classes_data[class_name]['rules_element'] = rules_element
        
        print(f"  Переменные: {class_variables}")

  
    
    rule_counter = 1
    
    # Создаем правило для каждой формулы
    for formula_info in all_formulas_info:
        class_name = formula_info['class']
        original_formula = formula_info['original']
        left_part = formula_info['left']
        right_part = formula_info['right']
        template = formula_info['template']
        
        # Находим переменные в правой части (кроме левой части)
        original_vars = re.findall(r'\b[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\b', right_part)
        original_vars = [v for v in original_vars if v != left_part]
        original_vars = sorted(set(original_vars), key=lambda x: right_part.index(x) if x in right_part else len(right_part))
        
        # Находим переменные в шаблоне (a, b, c, ...)
        template_vars = re.findall(r'\b[a-z]\b', template[2:])
        template_vars = sorted(set(template_vars))
        
        # Создаем маппинг: шаблонная переменная -> оригинальная переменная
        var_mapping = {}
        if len(original_vars) == len(template_vars):
            for i, t_var in enumerate(template_vars):
                if i < len(original_vars):
                    var_mapping[t_var] = original_vars[i]
        
        # Обратный маппинг (оригинальная -> шаблонная)
        rev_var_mapping = {}
        for key, value in var_mapping.items():
            rev_var_mapping[value] = key
        
        # Если маппинг успешен и есть relation для этого шаблона
        if var_mapping and template in template_to_relation:
            # Определяем входные параметры (оригинальные имена)
            input_params = []
            for t_var in template_vars:
                if t_var in var_mapping:
                    input_params.append(var_mapping[t_var])
            
            # Определяем выходной параметр (левая часть формулы)
            output_param = left_part
            
            # Получаем имя relation для этого шаблона
            relation_name = template_to_relation[template]
            
            # Получаем элемент правил для этого класса
            class_rules_element = classes_data[class_name]['rules_element']
            
            if class_rules_element is None:
                print(f"  ✗ Не найден элемент правил для класса {class_name}")
                continue
                
            # Создаем правило В ПРАВИЛЬНОМ МЕСТЕ (во вложенном классе)
            try:
                creator.add_rule(
                    class_rules_element,  # Используем rules элемента класса, а не main_rules!
                    rule_name=f"rule_{rule_counter}",
                    relation_name=relation_name,
                    input_params=input_params,
                    output_param=output_param,
                    class_names=[class_name],
                    reverse_map=rev_var_mapping
                )

                rule_counter += 1
            except Exception as e:
                print(f"Ошибка создания правила: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f" Не удалось создать правило: маппинг неудачен")

    ################# Сохранение XML файла
    
    tree = etree.ElementTree(model)
    
    with open("MIVAR1.xml", "wb") as f:
        tree.write(f, encoding="utf-8", pretty_print=True, xml_declaration=True)
    
def create_formula_template(left_part, right_part):
  
    original_no_spaces = f"{left_part}={right_part}".replace(" ", "")
    
    template = "y="
    
    # Находим все переменные в правой части
    right_vars = re.findall(r'\b[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\b', right_part)
    
    # Создаем словарь замен с сохранением порядка
    var_mapping = {}
    var_counter = 0
    var_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    
    # Токенизация правой части
    tokens = re.findall(r'[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\^\d+|[a-zA-Zα-ωΑ-ΩΔ][a-zA-zα-ωΑ-Ω0-9_]*|\d+\^\d+|\S', right_part)
    
    result_tokens = []
    for token in tokens:
        # Проверяем, является ли токен переменной со степенью
        if re.match(r'^[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\^\d+$', token):
            # Разделяем переменную и степень
            var_part, exp_part = token.split('^')
            
            if var_part != left_part and not var_part.isdigit():
                if var_part not in var_mapping:
                    var_mapping[var_part] = var_letters[var_counter]
                    var_counter += 1
                
                # Заменяем var_part на шаблонную переменную, оставляя степень
                result_tokens.append(f"{var_mapping[var_part]}^{exp_part}")
            else:
                result_tokens.append(token)
        
        # Проверяем, является ли токен простой переменной
        elif (re.match(r'^[a-zA-Zα-ωΑ-ΩΔ]', token) and 
            token != left_part and
            not token.isdigit() and
            '^' not in token):  # Убеждаемся, что это не выражение со степенью
            
            if token not in var_mapping:
                var_mapping[token] = var_letters[var_counter]
                var_counter += 1
            
            result_tokens.append(var_mapping[token])
        else:
            result_tokens.append(token)
    
    template_right = ''.join(result_tokens)
    
    # Заменяем степени на вызовы Math.pow
    def replace_pow(match):
        var = match.group(1)
        exp = match.group(2)
        return f"Math.pow({var}, {exp})"
    
    # Заменяем выражения вида a^2
    template_right = re.sub(r'([a-zA-Z])\^(\d+)', replace_pow, template_right)
    
    # Заменяем выражения вида (a+b)^2
    def replace_complex_pow(match):
        expr = match.group(1)
        exp = match.group(2)
        return f"Math.pow({expr}, {exp})"
    
    template_right = re.sub(r'\(([^)]+)\)\^(\d+)', replace_complex_pow, template_right)
    
    template += template_right.replace(" ", "")
    
    return template

if __name__ == "__main__":
    main()
