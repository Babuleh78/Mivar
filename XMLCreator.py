from lxml import etree
import uuid


class XMLCreator:
    def __init__(self):
        self.parameter_ids = {}  # Словарь для хранения соответствия имен параметров и их ID
        self.relations = [] # Список для хранения созданных relations
    
    def create_main_class(self, model, short_name="DefaultName", relations_list=None):
        main_class_elem = etree.SubElement(model, "class",
                                           id=f"{{{str(uuid.uuid4())}}}",
                                           shortName=short_name)
        main_class_elem.text = "\n"
        
        parameters = etree.SubElement(main_class_elem, "parameters")
        rules = etree.SubElement(main_class_elem, "rules")
        constraints = etree.SubElement(main_class_elem, "constraints")
        classes_elem = etree.SubElement(main_class_elem, "classes")
        
        parameters.tail = "\n"
        rules.text = "\n"
        rules.tail = "\n"
        constraints.tail = "\n"
        classes_elem.text = "\n"  
        classes_elem.tail = "\n"

        relations = etree.SubElement(model, "relations")
        relations.text = "\n"
        
        if relations_list:
            for rel in relations_list:
                self._add_relation(relations, rel)
        
        relations.tail = "\n"

        return main_class_elem, parameters, rules, constraints, classes_elem, relations
    
    def _add_relation(self, relations_elem, rel_data):
        relation_id = str(uuid.uuid4())
        if isinstance(rel_data, dict):
            shortName = rel_data.get('shortName', '')
            inObj = rel_data.get('inObj', ' ')
            outObj = rel_data.get('outObj', ' ')
            relationType = rel_data.get('relationType', 'simple')
            formula = rel_data.get('formula', '')
            
            new_relation = etree.SubElement(relations_elem, "relation",
                                            id=relation_id,
                                            shortName=shortName,
                                            inObj=inObj,
                                            relationType=relationType,
                                            outObj=outObj)
            if formula:
                new_relation.text = formula
            
            # Сохраняем информацию о relation для использования в rules
            self.relations.append({
                'id': relation_id,
                'shortName': shortName,
                'inObj': inObj,
                'outObj': outObj
            })
        else:
            new_relation = etree.SubElement(relations_elem, "relation",
                                            id=relation_id,
                                            shortName=str(rel_data),
                                            inObj=" ",
                                            outObj=" ")
        
        new_relation.tail = "\n"
        
        if len(relations_elem) > 1:
            prev_relation = relations_elem.getchildren()[-2]
            prev_relation.tail = "\n"
        
        return new_relation
    
    def create_class(self, parent, short_name="Вложенный класс", is_nested=False, 
                 class_id=None, parameters_list=None, additional_info=None):
    
        if class_id is None:
            class_id = str(uuid.uuid4())
        
        id_str = class_id if is_nested else f"{{{class_id}}}"
        
        new_class = etree.SubElement(parent, "class",
                                    id=id_str,
                                    shortName=short_name)
        
        new_class.text = "\n"
        
        parameters = etree.SubElement(new_class, "parameters")
        
        if parameters_list and len(parameters_list) > 0:
            parameters.text = "\n"
            for param_name in parameters_list:
                param_id = str(uuid.uuid4())
                
                # Сохраняем соответствие имени параметра и его ID
                key = f"{short_name}:{param_name}"
                self.parameter_ids[key] = param_id
                
                # Создаем базовые атрибуты параметра
                param_attrs = {
                    "id": param_id,
                    "shortName": param_name,
                    "type": "double"
                }
                
                # Добавляем дополнительные атрибуты, если они есть
                if additional_info and param_name in additional_info:
                    descr, start_value = additional_info[param_name]
                    
                    # Проверяем, что значения не None и не пустые
                    if descr is not None and str(descr).strip():
                        param_attrs["description"] = str(descr).strip()
                    
                    if start_value is not None and str(start_value).strip():
                        param_attrs["defaultValue"] = str(start_value).strip()
                
                # Создаем элемент parameter со всеми атрибутами
                param = etree.SubElement(parameters, "parameter", **param_attrs)
                param.tail = "\n"
            
            if parameters.getchildren():
                last_param = parameters.getchildren()[-1]
                last_param.tail = None
        
        parameters.tail = "\n"
        
        # Создаем остальные элементы
        rules = etree.SubElement(new_class, "rules")
        rules.text = "\n"
        rules.tail = "\n"
        
        constraints = etree.SubElement(new_class, "constraints")
        classes_elem = etree.SubElement(new_class, "classes")
        
        constraints.tail = "\n"
        classes_elem.tail = "\n"
        
        new_class.tail = "\n"
        
        return new_class, parameters
    
    def add_rule(self, rules_elem, rule_name, relation_name, 
                 input_params, output_param,  reverse_map, class_names=None, ):
       
        relation_id = None
        for rel in self.relations:
            if rel['shortName'] == relation_name:
                relation_id = rel['id']
                break
        
        if not relation_id:
            raise ValueError(f"Relation с именем '{relation_name}' не найден")
        
        result_key = None
        if class_names and len(class_names) > 0:
            for class_name in class_names:
                result_key = f"{class_name}:{output_param}"
                if result_key in self.parameter_ids:
                    break
        else:
            for key in self.parameter_ids:
                if key.endswith(f":{output_param}"):
                    result_key = key
                    break
        
        if not result_key or result_key not in self.parameter_ids:
            raise ValueError(f"Параметр '{output_param}' не найден")
        
        
        # result_id = f"{output_param}:{self.parameter_ids[result_key]}"
        result_id = f"y:{self.parameter_ids[result_key]}"
        
        init_parts = []
        for param_name in input_params:
            param_key = None
            
            if class_names and len(class_names) > 0:
                for class_name in class_names:
                    param_key = f"{class_name}:{param_name}"
                    
                    if param_key in self.parameter_ids:
                        break
            else:
                for key in self.parameter_ids:
                    if key.endswith(f":{param_name}"):
                        param_key = key
                        break
            
            if not param_key or param_key not in self.parameter_ids:
                raise ValueError(f"Параметр '{param_name}' не найден")
            
            init_parts.append(f"{reverse_map[param_name]}:{self.parameter_ids[param_key]}")
        
        init_id = ";".join(init_parts)
        
        rule_id = str(uuid.uuid4())
        rule_elem = etree.SubElement(rules_elem, "rule",
                                     id=rule_id,
                                     shortName=rule_name,
                                     relation=relation_id,
                                     resultId=result_id,
                                     initId=init_id)
        
        if len(rules_elem) > 1:
            prev_rule = rules_elem.getchildren()[-2]
            prev_rule.tail = "\n"
        
        rule_elem.tail = "\n"
        
        return rule_elem
