import pandas as pd
import re
import uuid
import os
from lxml import etree
from XMLCreator import XMLCreator
from FormulaCreator import FormulaCreator
from FormulaProcessor import FormulaProcessor, FormulaRegistry


class ExcelProcessor:
    """Класс для обработки Excel файлов и создания XML с правилами"""
    
    def __init__(self):
        self.formula_registry = FormulaRegistry()
        self.classes_data = {}
        self.processed_excel_path = None
        self.relations_list = []
        
    @staticmethod
    def is_negative_expression(right_part):
        """Проверяет, является ли выражение отрицательным"""
        stripped = right_part.strip()
        return stripped.startswith('-')
    
    @staticmethod
    def filter_ambiguous_variants(formula_list):
        """Фильтрует неоднозначные варианты формул"""
        if not formula_list:
            return []
        
        if len(formula_list) == 1:
            return formula_list
        
        # Разделяем на положительные и отрицательные варианты
        positive = []
        negative = []
        
        for formula in formula_list:
            if ExcelProcessor.is_negative_expression(formula['right']):
                negative.append(formula)
            else:
                positive.append(formula)
        
        # Приоритет: оставляем только положительные варианты
        if positive:
            return positive
        
        # Если только отрицательные — возвращаем один вариант
        if negative:
            return [negative[0]]
        
        return formula_list
    
    def process_additional_info(self, cell_value, class_name):
        """Обрабатывает дополнительную информацию о переменных"""
        if ':' in cell_value:
            # Формат: P:"Мощность"
            parts = cell_value.split(':', 1)
            if len(parts) == 2:
                var_name = parts[0].strip()
                description = parts[1].strip().strip('"')
                
                if var_name not in self.classes_data[class_name]['additional_info']:
                    self.classes_data[class_name]['additional_info'][var_name] = (description, None)
                else:
                    old_descr, old_val = self.classes_data[class_name]['additional_info'][var_name]
                    self.classes_data[class_name]['additional_info'][var_name] = (description, old_val)
                
                self.classes_data[class_name]['variables'].add(var_name)
                
        elif '=' in cell_value and not any(sym in cell_value for sym in '+-*/^()'):
            # Формат: t=1
            parts = cell_value.split('=', 1)
            if len(parts) == 2:
                var_name = parts[0].strip()
                default_value = parts[1].strip()
                
                if var_name not in self.classes_data[class_name]['additional_info']:
                    self.classes_data[class_name]['additional_info'][var_name] = (None, default_value)
                else:
                    old_descr, old_val = self.classes_data[class_name]['additional_info'][var_name]
                    self.classes_data[class_name]['additional_info'][var_name] = (old_descr, default_value)
                
                self.classes_data[class_name]['variables'].add(var_name)
    
    def process_excel_file(self, excel_file, output_folder=None):
        # Инициализируем FormulaCreator для предобработки
        fc = FormulaCreator()
        
        # Определяем путь для обработанного Excel
        if output_folder:
            base_name = os.path.basename(excel_file)
            name_without_ext = os.path.splitext(base_name)[0]
            processed_excel = os.path.join(output_folder, f"{name_without_ext}_MIVAR.xlsx")
        else:
            processed_excel = fc.process_excel_by_column(excel_file)
        
        # Обрабатываем Excel
        processed_excel = fc.process_excel_by_column(excel_file, processed_excel)
        self.processed_excel_path = processed_excel
        
        # Читаем все листы Excel
        df = pd.read_excel(processed_excel, sheet_name=None, dtype=str)
        
        # Очищаем данные перед новой обработкой
        self.formula_registry = FormulaRegistry()
        self.classes_data = {}
        
        # Обрабатываем каждый лист
        for sheet_name, sheet_data in df.items():
            for col_idx, col_name in enumerate(sheet_data.columns):
                # Создаем запись для класса, если его еще нет
                if col_name not in self.classes_data:
                    self.classes_data[col_name] = {
                        'variables': set(),
                        'formulas': [],
                        'raw_formulas': {},
                        'additional_info': {},
                        'xml_element': None,
                        'rules_element': None
                    }
                
                is_main_part = True
                # Обрабатываем ячейки в этом столбце
                for cell_value in sheet_data[col_name]:
                    if pd.notna(cell_value) and isinstance(cell_value, str):
                        cell_value = str(cell_value).strip()
                        
                        if is_main_part and cell_value == "Дополнительно":
                            is_main_part = False
                            continue
                        
                        if is_main_part:
                            if FormulaProcessor.is_formula(cell_value):
                                # Ищем переменные в формуле
                                words = FormulaProcessor.extract_variables(cell_value)
                                self.classes_data[col_name]['variables'].update(words)
                                
                                # Обрабатываем формулу, если она содержит '='
                                if '=' in cell_value:
                                    left_part, right_part = cell_value.split('=', 1)
                                    left_part = left_part.strip()
                                    right_part = right_part.strip()
                                    
                                    # Добавляем левую часть как переменную
                                    self.classes_data[col_name]['variables'].add(left_part)
                                    
                                    # Накапливаем сырые формулы
                                    if left_part not in self.classes_data[col_name]['raw_formulas']:
                                        self.classes_data[col_name]['raw_formulas'][left_part] = []
                                    
                                    self.classes_data[col_name]['raw_formulas'][left_part].append({
                                        'original': cell_value,
                                        'left': left_part,
                                        'right': right_part,
                                        'variables': words
                                    })
                        else:
                            # Обработка дополнительной информации
                            self.process_additional_info(cell_value, col_name)
        
        # Выполняем после полной обработки всех листов
        for class_name, class_data in self.classes_data.items():
            for left_part, formula_list in class_data['raw_formulas'].items():
                # Фильтруем неоднозначные варианты
                filtered_formulas = self.filter_ambiguous_variants(formula_list)
                
                for formula_data in filtered_formulas:
                    left_part = formula_data['left']
                    right_part = formula_data['right']
                    original = formula_data['original']
                    words = formula_data['variables']
                    
                    # Создаем шаблон формулы
                    template, canonical_template = FormulaProcessor.create_formula_template(
                        left_part, right_part
                    )
                    
                    # Проверяем на дубликаты
                    if not self.formula_registry.is_duplicate(canonical_template, left_part):
                        # Сохраняем информацию о формуле
                        formula_info = {
                            'class': class_name,
                            'original': original,
                            'left': left_part,
                            'right': right_part,
                            'template': template,
                            'canonical_template': canonical_template,
                            'variables': words
                        }
                        
                        self.formula_registry.add_formula(formula_info)
                        class_data['formulas'].append(formula_info)
            
            # Удаляем временное хранилище
            if 'raw_formulas' in class_data:
                del class_data['raw_formulas']
        
        return self.classes_data, self.formula_registry, processed_excel
    
    def create_xml_with_rules(self, filename):
        # Создаем отношения из реестра формул
        self.relations_list = self.formula_registry.create_relations()
        
        # Инициализируем XMLCreator
        creator = XMLCreator()
        
        # Создаем корневой элемент model
        model = etree.Element("model", 
                              id=f"{{{str(uuid.uuid4())}}}",
                              shortName=str(filename),
                              formatXmlVersion="2.0",
                              description=str(filename))
        model.text = "\n"
        
        # Создаем основной класс
        main_class_elem, main_params, main_rules, main_constraints, classes_elem, relations_elem = creator.create_main_class(
            model, 
            str(filename),
            relations_list=self.relations_list
        )
        
        # Создаем вложенные классы
        for class_idx, class_name in enumerate(self.classes_data.keys(), 1):
            print(f"Создание класса {class_idx}: {class_name}")
            
            class_variables = list(self.classes_data[class_name]['variables'])
            additional_info = self.classes_data[class_name].get('additional_info', {})
            
            nested_class, nested_params = creator.create_class(
                classes_elem, 
                class_name,
                is_nested=True,
                parameters_list=class_variables,
                additional_info=additional_info
            )
            
            self.classes_data[class_name]['xml_element'] = nested_class
            self.classes_data[class_name]['rules_element'] = nested_class.find("rules")
            
            print(f"  Переменные: {len(class_variables)}")
        
        # Создаем правила для формул
        rule_counter = self.create_rules_for_classes(creator)
        
        # Сохраняем XML файл
        tree = etree.ElementTree(model)
        with open(filename, "wb") as f:
            tree.write(f, encoding="utf-8", pretty_print=True, xml_declaration=True)
        
        return len(self.relations_list), len(self.classes_data), rule_counter
    
    def create_rules_for_classes(self, creator):
        """Создает правила для всех классов"""
        rule_counter = 1
        
        for formula_info in self.formula_registry.get_all_formulas():
            class_name = formula_info['class']
            original_formula = formula_info['original']
            left_part = formula_info['left']
            right_part = formula_info['right']
            canonical_template = formula_info['canonical_template']
            
            # Получаем оригинальные переменные
            original_vars = FormulaProcessor.extract_variables(right_part, exclude=left_part)
            original_vars = sorted(set(original_vars), key=lambda x: right_part.index(x) if x in right_part else len(right_part))
            
            # Получаем переменные из шаблона
            template_vars = re.findall(r'\b[a-z]\b', canonical_template[2:])
            template_vars = sorted(set(template_vars))
            
            # Создаем маппинг переменных
            var_mapping, rev_var_mapping = FormulaProcessor.create_var_mapping(
                original_vars, template_vars
            )
            
            # Получаем имя отношения
            relation_name = self.formula_registry.get_relation_name(canonical_template)
            if not relation_name:
                print(f"  Не найден relation для шаблона: {canonical_template}")
                continue
            
            # Получаем элемент правил для класса
            class_rules_element = self.classes_data[class_name]['rules_element']
            if class_rules_element is None:
                print(f"  Не найден элемент правил для класса {class_name}")
                continue
            
            # Создаем правило
            input_params = [var_mapping.get(t_var, t_var) for t_var in template_vars]
            output_param = left_part
            rule_name_str = original_formula.replace(" ", "")
            
            try:
                creator.add_rule(
                    class_rules_element,
                    rule_name=rule_name_str,
                    relation_name=relation_name,
                    input_params=input_params,
                    output_param=output_param,
                    class_names=[class_name],
                    reverse_map=rev_var_mapping
                )
                print(f"  Создано правило {rule_counter}: {rule_name_str}")
                rule_counter += 1
            except Exception as e:
                print(f"Ошибка создания правила: {e}")
                import traceback
                traceback.print_exc()
        
        return rule_counter - 1
    
    def process(self, input_file, output_folder=None, xml_filename="MIVAR.xml"):
        # Обрабатываем Excel файл
        classes_data, formula_registry, processed_excel = self.process_excel_file(
            input_file, output_folder
        )
        
        print(f"Обработано формул: {len(formula_registry.get_all_formulas())}")
        print(f"Уникальных канонических шаблонов: {len(formula_registry.canonical_templates)}")
        
        # Определяем путь для XML
        if output_folder:
            xml_path = os.path.join(output_folder, xml_filename)
        else:
            xml_path = xml_filename
        
        # Создаем XML с правилами
        print("\nСоздаем XML файл...")
        relations_count, classes_count, rules_count = self.create_xml_with_rules(xml_path)
        
        print(f"\nРезультаты обработки:")
        print(f"- Отношений: {relations_count}")
        print(f"- Классов: {classes_count}")
        print(f"- Правил: {rules_count}")
        print(f"- Формул в реестре: {len(formula_registry.get_all_formulas())}")
        print(f"- Обработанный Excel: {processed_excel}")
        print(f"- XML файл: {xml_path}")
        
        return {
            'relations': relations_count,
            'classes': classes_count,
            'rules': rules_count,
            'formulas': len(formula_registry.get_all_formulas()),
            'excel_path': processed_excel,
            'xml_path': xml_path
        }
