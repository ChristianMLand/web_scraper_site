from abc import ABC,abstractmethod

container_size_aliases = {
    "20" : ["20DR"],
    "Reefer" : ["20RFR", "40RFR"],
    "HT/OT" : ["Special"],
    "FR" : ["Special"],
    "OT" : ["Special"],
    "HT" : ["Special"],
    "40RH" : ["40RFR"],
    "20RH" : ["20RFR"],
    "NONE" : []
}

class TerminalParser(ABC):
    def __init__(self):
        self.container_sizes = []
        self.ssl_names = []
        self.data = {}

    @staticmethod
    def get_parser(terminal_name) -> 'TerminalParser':
        terminals = {
            "t18" : T18Parser,
            "t30" : T30Parser,
            "t5" : T5Parser,
            "wut" : WUTParser,
            "husky" : HuskyParser
        }
        return terminals[terminal_name]()

    def parse(self, soup):
        tables = self.get_tables(soup)
        for x, table in enumerate(tables):
            rows = self.get_rows(table)
            self.get_container_sizes(table)
            self.get_ssl_names(rows)
            for i, tr in enumerate(rows):
                info_dict = {}
                for j, td in enumerate(self.get_tds(tr)):
                    containers = [self.container_sizes[j]]
                    if containers[0] in container_size_aliases:
                        containers = container_size_aliases[containers[0]]
                    for container in containers:
                        td_content = self.clean_text(td)
                        if td_content in ["YES", "OPEN"]:
                            availability_type = self.get_type(x if len(tables) > 1 else j)
                            for line in self.ssl_names[i].split('/'):#TODO move this up out of for loop
                                if line not in self.data:
                                    self.data[line] = info_dict
                                else:
                                    info_dict = self.data[line]
                            if container in info_dict:
                                info_dict[container].append(availability_type)
                            else:
                                info_dict[container] = [availability_type]
        return self.data

    def clean_text(self, elem):
        return elem.getText().replace("’ ","").replace("Pick","").replace(" Up", "").replace("Drop", "").replace("' ","").strip()

    def get_type(self, index):
        return "Pick" if index % 2 else "Drop"

    def get_ssl_names(self, rows):
        for tr in rows:
            line = self.clean_text(tr.td).replace("YES","")
            if line not in self.ssl_names:
                self.ssl_names.append(line)

    def get_tds(self, row):
        return row.find_all("td")[1:]

    @abstractmethod
    def get_tables(self, soup):
        ...

    @abstractmethod
    def get_rows(self, table):
        ...

    @abstractmethod
    def get_container_sizes(self, table):
        ...

class T18Parser(TerminalParser):
    def get_tables(self, soup):
        return [soup.find_all("table")[1]]

    def get_rows(self, table):
        return table.find_all("tr")[1:14]

    def get_container_sizes(self, table):
        self.container_sizes = [self.clean_text(td) for td in self.get_tds(table.tr)]

class T30Parser(TerminalParser):
    def get_container_sizes(self, table):
        return super().get_container_sizes(table)

    def get_rows(self, table):
        return table.find_all("tr")[1:]

    def get_tables(self, soup):
        return [soup.find_all("table")[3].tbody]
    
    def get_ssl_names(self, rows):
        self.ssl_names = [self.clean_text(tr.td) for tr in rows]
    
    def get_type(self, index):
        return "Drop"

    def parse(self, soup):#TODO handle picks as well
        table = self.get_tables(soup)[0]
        rows = self.get_rows(table)
        self.get_ssl_names(rows)
        for i, tr in enumerate(rows):
            info_dict = {}
            containers = self.clean_text(self.get_tds(tr)[0]).split(',')
            availability_type = self.get_type(i)
            for line in self.ssl_names[i].split('/'):
                if line not in self.data:
                    self.data[line] = info_dict
            for y, container in enumerate(containers):
                if container in container_size_aliases:
                    containers.pop(y)
                    containers += container_size_aliases[container]
            for cont in containers:
                info_dict[cont] = [availability_type]
        return {k:v for k,v in self.data.items() if v}

class T5Parser(TerminalParser):
    def get_tables(self, soup):
        return soup.find_all("table")[1:]

    def get_rows(self, table):
        return table.find_all("tr")[1:]

    def get_container_sizes(self, table):
        self.container_sizes = [self.clean_text(td) for td in self.get_tds(table.tr)]

class WUTParser(TerminalParser):
    def get_tables(self, soup):
        return [soup.find_all("table")[0].tbody]

    def get_rows(self, table):
        return table.find_all("tr")[1:]

    def get_container_sizes(self, table):
        self.container_sizes = [self.clean_text(td) for td in self.get_tds(table.tr)]

class HuskyParser(TerminalParser):
    def get_tables(self, soup):
        return [soup.find_all("table")[2]]

    def get_rows(self, table):
        return table.tbody.find_all("tr")

    def get_tds(self, row):
        return row.find_all("td")[2:]

    def get_container_sizes(self, table):
        self.container_sizes = [self.clean_text(td) for td in table.thead.tr.find_all("th")[2:]]

    def get_ssl_names(self, rows):
        for tr in rows:
            line = self.clean_text(tr.find_all("td")[1])
            if line not in self.ssl_names:
                self.ssl_names.append(line)