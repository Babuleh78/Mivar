from lxml import etree
import uuid

def create_main_class(model, short_name="DefaultName"):
    main_class_elem = etree.SubElement(model, "class",
                                       id=f"{{{str(uuid.uuid4())}}}",
                                       shortName=short_name)
    main_class_elem.text = "\n"
    
    parameters = etree.SubElement(main_class_elem, "parameters")
    rules = etree.SubElement(main_class_elem, "rules")
    constraints = etree.SubElement(main_class_elem, "constraints")
    classes_elem = etree.SubElement(main_class_elem, "classes")
    
    parameters.tail = "\n"
    rules.tail = "\n"
    constraints.tail = "\n"
    classes_elem.text = "\n"  
    classes_elem.tail = "\n"

    relations = etree.SubElement(model, "relations")
    relations.tail = "\n"

    return main_class_elem, parameters, rules, constraints, classes_elem


def create_class(parent, short_name="Одна модель", is_nested=False, parameters_list=None):
   
    class_id = str(uuid.uuid4())
    
    if is_nested:
        id_str = class_id  
    else:
        id_str = f"{{{class_id}}}"
    
    new_class = etree.SubElement(parent, "class",
                              id=id_str,
                              shortName=short_name)
    
    new_class.text = "\n"
    
    # Создаем элемент parameters
    parameters = etree.SubElement(new_class, "parameters")
    
    # Добавляем параметры, если они переданы
    if parameters_list and len(parameters_list) > 0:
        parameters.text = "\n"
        for param_name in parameters_list:
            param_id = str(uuid.uuid4())
            new_param = etree.SubElement(parameters, "parameter",
                                       id=param_id,
                                       shortName=str(param_name),
                                       type="double")
            new_param.tail = "\n"
        
        # Убираем tail у последнего параметра
        if parameters.getchildren():
            last_param = parameters.getchildren()[-1]
            last_param.tail = None
    
    parameters.tail = "\n"
    
    # Создаем остальные элементы
    rules = etree.SubElement(new_class, "rules")
    constraints = etree.SubElement(new_class, "constraints")
    classes_elem = etree.SubElement(new_class, "classes")
    
    rules.tail = "\n"
    constraints.tail = "\n"
    
    if is_nested:
        # Для вложенных классов - пустой classes
        classes_elem.tail = "\n"
    else:
        # Для основного класса - возможно добавление вложенных
        classes_elem.text = "\n" 
        classes_elem.tail = "\n"
    
    new_class.tail = "\n" if parent.tag == "classes" else "\n"
    
    return new_class


def create_xml():
    model = etree.Element("model", 
                          id=f"{{{str(uuid.uuid4())}}}",
                          shortName="Одна модель",
                          formatXmlVersion="2.0",
                          description="Model 1")
    
    model.text = "\n"

    main_class_elem, main_params, main_rules, main_constraints, classes_elem = create_main_class(model, "Одна модель")
   
    nested_class2 = create_class(classes_elem, 
                                 "Вложенный класс 2", 
                                 is_nested=True,
                                 parameters_list=["c"])
    
    nested_class1 = create_class(classes_elem, 
                                 "Вложенный класс 1", 
                                 is_nested=True,
                                 parameters_list=["b", "a"])
    
    # Устанавливаем tail для основного класса
    main_class_elem.tail = "\n"
    # main_class_elem.tail = "\n"
    
    # relations = etree.SubElement(model, "relations")
    # relations.tail = "\n"
    
    # Создаем и сохраняем дерево
    tree = etree.ElementTree(model)
    
    with open("physics_model.xml", "wb") as f:
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding="utf-8", pretty_print=False)
    
    print("XML файл создан: physics_model.xml")
    
    xml_str = etree.tostring(model, encoding="utf-8", pretty_print=False).decode('utf-8')
    print("Содержимое XML:")
    print(xml_str)
    
    return tree

if __name__ == "__main__":
    create_xml()
