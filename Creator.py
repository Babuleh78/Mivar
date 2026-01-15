import pandas as pd
import re
from XMLCreator import XMLCreator
from lxml import etree
import uuid

def main():
    EXCEL_FILE = "move.xlsx" 

    df = pd.read_excel(EXCEL_FILE, sheet_name=None, dtype=str)

    variables_set = set()
    formulas_dict = {}


    for sheet_name, sheet_data in df.items():
        first_column = sheet_data.columns[0]
        
        for index, value in sheet_data[first_column].items():
            if pd.notna(value) and isinstance(value, str):
                value = str(value).strip()
                
                if any(sym in value for sym in '=+-*/^()'):
                    words = re.findall(r'\b[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\b', value)
                    variables_set.update(words)
                    
                    # Создаем шаблон формулы
                    if '=' in value:
                        left_part, right_part = value.split('=', 1)
                        left_part = left_part.strip()
                        right_part = right_part.strip()
                        
                        original_no_spaces = f"{left_part}={right_part}".replace(" ", "")
                        
                        template = "y="
                        
                        # Находим все переменные в правой части
                        right_vars = re.findall(r'\b[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\b', right_part)
                        
                        # Создаем словарь замен с сохранением порядка
                        var_mapping = {}
                        var_counter = 0
                        var_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
                                    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
                    
                        tokens = re.findall(r'[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\^\d+|[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*|\d+\^\d+|\S', right_part)
                        
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
                     
                        # Используем регулярное выражение для поиска выражений вида "переменная^число"
                        def replace_pow(match):
                            var = match.group(1)  # переменная
                            exp = match.group(2)  # степень
                            return f"Math.pow({var}, {exp})"
                        
                        # Заменяем все a^2, b^3 и т.д. на Math.pow(a, 2), Math.pow(b, 3)
                        template_right = re.sub(r'([a-zA-Z])\^(\d+)', replace_pow, template_right)
                        
                        # Также заменяем выражения вида (a+b)^2 на Math.pow((a+b), 2)
                        # Это более сложная замена для выражений в скобках
                        def replace_complex_pow(match):
                            expr = match.group(1)  # выражение в скобках
                            exp = match.group(2)   # степень
                            return f"Math.pow({expr}, {exp})"
                        
                        # Заменяем выражения вида (a+b)^2 на Math.pow((a+b), 2)
                        template_right = re.sub(r'\(([^)]+)\)\^(\d+)', replace_complex_pow, template_right)
                        
                        template += template_right.replace(" ", "")
                        
                        if template not in formulas_dict:
                            formulas_dict[template] = []
                        formulas_dict[template].append(value)

    ################# Преобразование шаблонов формул в relations_list
    
    relations_list = []
    
    for template_idx, (template, formulas) in enumerate(formulas_dict.items(), 1):
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
            
            relation = {
                'shortName': f"Rule_{template_idx}",
                'inObj': in_obj,
                'outObj': out_obj,
                'relationType': 'simple',
                'formula': template 
            }
            
            relations_list.append(relation)

    ################# Запись переменных в parameters_list
    parameters_list = []

    for el in variables_set:
        parameters_list.append(str(el))

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

    nested_class1, nested1_params = creator.create_class(
        classes_elem, 
        "Задачи на движение",
        is_nested=True,
        parameters_list=parameters_list
    )

    ################# СОЗДАНИЕ ПРАВИЛ (RULES) ИЗ ШАБЛОНОВ
    
    print("\n" + "="*60)
    print("СОЗДАНИЕ ПРАВИЛ ИЗ ШАБЛОНОВ:")
    print("="*60)
    
    # Для каждого шаблона создаем правило
    for template_idx, (template, formulas) in enumerate(formulas_dict.items(), 1):
        print(f"\nШаблон {template_idx}: {template}")
        print(f"Количество формул: {len(formulas)}")
        
        # Берем первую формулу из списка для примера
        if formulas:
            example_formula = formulas[0]
            print(f"Пример формулы: {example_formula}")
            
            # Разбираем пример формулы, чтобы понять соответствие переменных
            if '=' in example_formula:
                left_part, right_part = example_formula.split('=', 1)
                left_part = left_part.strip()
                right_part = right_part.strip()
                
                # Находим переменные в оригинальной формуле
                original_vars = re.findall(r'\b[a-zA-Zα-ωΑ-ΩΔ][a-zA-Zα-ωΑ-Ω0-9_]*\b', right_part)
                original_vars = [v for v in original_vars if v != left_part]
                original_vars = sorted(set(original_vars), key=lambda x: right_part.index(x))
                
                # Находим переменные в шаблоне (a, b, c, ...)
                template_vars = re.findall(r'\b[a-z]\b', template[2:])
                template_vars = sorted(set(template_vars))
                
                # Создаем маппинг: шаблонная переменная -> оригинальная переменная
                var_mapping = {}
                if len(original_vars) == len(template_vars):
                    for i, t_var in enumerate(template_vars):
                        if i < len(original_vars):
                            var_mapping[t_var] = original_vars[i]
                
                rev_var_mapping = {}
                for key, value in var_mapping.items():
                    rev_var_mapping[value] = key
                
                print(rev_var_mapping)
                # Если маппинг успешен, создаем правило
                if var_mapping:
                    # Определяем входные параметры (оригинальные имена)
                    input_params = []
                    for t_var in template_vars:
                        if t_var in var_mapping:
                            input_params.append(var_mapping[t_var])
                    
                    # Определяем выходной параметр (левая часть формулы)
                    output_param = left_part
                    print(output_param, input_params)
                    # Создаем правило
                    try:
                        creator.add_rule(
                            main_rules,
                            rule_name=f"rule_{template_idx}",
                            relation_name=f"Rule_{template_idx}",
                            input_params=input_params,
                            output_param=output_param,
                            class_names=["Задачи на движение"],
                            reverse_map = rev_var_mapping
                        )
                        print(f"✓ Создано правило rule_{template_idx}")
                        print(f"  Входные параметры: {input_params}")
                        print(f"  Выходной параметр: {output_param}")
                    except Exception as e:
                        print(f"✗ Ошибка создания правила: {e}")
                else:
                    print(f"✗ Не удалось сопоставить переменные для шаблона {template}")


    tree = etree.ElementTree(model)
    
    with open("MIVAR1.xml", "wb") as f:
        tree.write(f, encoding="utf-8", pretty_print=False)
    
    print("XML файл создан: MIVAR1.xml")

if __name__ == "__main__":
    main()
