__author__ = 'marcos'
import argparse
import sys
import logging
import csv
from closeio_api import Client, APIError

log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

ERR_FILE_NOT_FOUND = 0
ERR_INVALID_FILE = 1
ERR_AUTHENTICATION_ERROR = 2
ERR_UNKNOWN_ERROR = 3
ERR_MISSING_CSV_HEADERS = 4

EXPECTED_HEADER_NAMES = ("tag", "custom_field_name", "custom_field_value")

ERROR_MESSAGES = {
    ERR_FILE_NOT_FOUND: "File not found, please check the filename you provided",
    ERR_INVALID_FILE:
        """File is not in the correct format, make sure it is a proper csv file with columns:\n
        tag: type string, the tag to be searched\n
        custom_field_name: The custom name field to be created if missing and then populated\n
        custom_field_value: the content to populate the custom field\n
        """,
    ERR_AUTHENTICATION_ERROR: "Could not authenticate to close.io api with the provided api key, please check it "
                              "and try again",
    ERR_UNKNOWN_ERROR: "There was an unidentified error, please contact support and provide the full output of this command",
    ERR_MISSING_CSV_HEADERS: "The input file has no headers"

}



class Reader:

    def __init__(self):
        self.tags_dict = dict()
        self.parser = argparse.ArgumentParser("Move tags to custom fields")
        self.parser.add_argument('--apikey', '-a', type=str, dest='apikey', required=True)
        self.parser.add_argument('--file', '-f', type=str, dest='filename', required=True)
        self.error_count = 0
        self.moved_tags = 0
        self.rejected_data = []


    def start_close_io_session(self):
        self.api = Client(self.apikey)
        try:
            test_call = self.api.get("lead")
        except APIError, e:
            logging.error(e)
            self.abort(ERR_AUTHENTICATION_ERROR)



    def abort(self, error_code):
        """
        :param error_code: One of the error code constants
        :return: A normalized status exit code from the ERROR_MESSAGES dict const
        """
        status_code = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES[ERR_UNKNOWN_ERROR])
        print("Command Aborted:\n{0}\n".format(status_code))
        sys.exit(error_code)

    def load_input_file(self):
        """
        Checks that the file provided is a well formed file, and then load it as an class attribute
        :param file: The file object that contains the csv input
        :return:
        """
        self.source = csv.DictReader(self.file)
        if self.source.fieldnames is None:
            self.abort(ERR_MISSING_CSV_HEADERS)
        log.info("Headers found in CSV Input File: %s", self.source.fieldnames)
        if not all(x in EXPECTED_HEADER_NAMES for x in self.source.fieldnames):
            self.abort(ERR_INVALID_FILE)
        self.input_row_count = self.source.line_num -1
        log.info("Content rows found in csf file %s", self.input_row_count )


    def process_row(self, row):
        pass


    def create_input_tags_dict(self):
        for row in self.source:
            self.tags_dict[row["tag"]] = {"field_name":row["custom_field_name"],
                                          "field_value":row["custom_field_value"]}



    def run(self):
        args=self.parser.parse_args()
        self.apikey = args.apikey
        try:
            self.file = open(args.filename, "r")
        except IOError:
            self.abort(ERR_FILE_NOT_FOUND)
        self.load_input_file()
        self.start_close_io_session()
        self.create_input_tags_dict()
        self.update_all_leads()
        logging.info("""Operation Completed:
        Moved Tags: {0}
        Unable to move: {1}
        """.format(self.moved_tags, self.error_count))
        if self.error_count > 0:
           errors_output = open("errors.txt", "w")
           for err in self.rejected_data:
                errors_output.write(err)
           errors_output.close()



    def update_all_leads(self):
        leads = self.api.get('lead')
        offset = 0
        has_more = True

        while(has_more):
            resp = self.api.get('lead', data={
                'query': 'sort:display_name',
                '_skip': offset

            })
            for lead_data in resp['data']:
                print lead_data
                custom_fields = lead_data.get("custom")
                if not custom_fields:
                    continue
                tags_field = custom_fields.get("Tags", None )
                logging.debug(tags_field)
                if tags_field:
                    tags = tags_field.split(",")
                    for tag in tags:
                        found_tag = self.tags_dict.get(tag.strip())
                        if found_tag:
                            logging.debug(found_tag)
                            data = {"custom.{0}".format(found_tag["field_name"]):found_tag["field_value"] }
                            try:
                                result = self.api.put('lead/'+lead_data['id'],
                                    data= data)
                                self.moved_tags+=1
                            except:
                                logging.warn("could not update lead id {0} with data {1}".format(lead_data["id"], data))
                                self.rejected_data.append((lead_data["id"], data))
                                self.error_count+=1


            has_more = resp["has_more"]



if __name__  == "__main__":
    Reader().run()