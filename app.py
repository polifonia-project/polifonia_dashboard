from flask import Flask, render_template, request, url_for, redirect, session
from flask_session import Session
import json
import github_sync
import conf

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SESSION_FILE_THRESHOLD'] = 100
Session(app)


def read_json(file_name):
    '''
    Open and read json file.

    Args:
        file_name (str): a string that specifies the name of the json file to read.

    Returns:
        data (dict): a dictionary containing the content of the json file.
    '''
    with open(file_name) as config_form:
        data = json.load(config_form)
        return data


def update_json(file_name, json_read):
    '''
    Update and dump a new json file.

    Args:
        file_name (str): a string that specifies the name of the json file to update.
        json_read (dict): the dictionary that contains data to update the json file.
    '''
    with open(file_name, 'w') as config_update:
        json.dump(json_read, config_update, indent=4)


def access_data_sources(section_name, datastory_name, file_name):
    '''
    This function accesses a specific datastory data in the config file based on its own and section names.

    Args:
        section_name (str): a string that identify the name of the section.
        datastory_name (str): a string that identify the data story name.
        file_name (str): a string that specifies the name of the json file to read.

    Returns:
        data (dict): a dictionary containing the data concerning the requested data story.
    '''
    for source, details in read_json(file_name)['data_sources'][section_name].items():
        if datastory_name == source:
            return details


def manage_datastory_data(general_data, file, section_name):
    '''
    This function deals with data story data after the submission of the WYSIWYG form.

    Args:
        general_data (dict): a dictionary containing data of the json fiile.
        file (str): a string that specifies the name of the json file to read.
        section_name (str): a string that identify the name of the section.

    Returns:
        datastory_name (str): a string that identifies the data story name.
    '''
    # get data and add to existing datastory instance in config

    # transform ImmutableMultiDict into regular dict
    form_data = request.form.to_dict(flat=True)
    datastory_title = form_data['title']

    dynamic_elements = []
    position_set = set()
    color_code_list = []

    for name, data in general_data['data_sources'].items():
        if name == section_name:
            for datastory, datastory_data in data.items():
                # with the title we check where to insert data
                if datastory == datastory_title.lower().replace(" ", "_"):
                    # we fill a set with the positions of the elements' type
                    for k, v in form_data.items():
                        if '__' in k:
                            position_set.add(int(k.split('__')[0]))
                        elif '_color' in k:
                            color_code_list.insert(0, v)
                        else:
                            datastory_data[k] = v

                    datastory_data['color_code'] = color_code_list
                    # we create as many dicts as there are positions, to store each type of element and append to
                    # dynamic_elements list
                    for position in position_set:
                        operations = []
                        op_list = []
                        elements_dict = {}
                        elements_dict['position'] = position
                        for k, v in form_data.items():
                            if '__' in k:
                                if position == int(k.split('__')[0]):
                                    if 'text' in k:
                                        elements_dict['type'] = 'text'
                                        elements_dict[k.split('__')[1]] = v
                                    elif 'count' in k:
                                        elements_dict['type'] = 'count'
                                        elements_dict[k.split('__')[1]] = v
                                    elif 'chart' in k:
                                        elements_dict['type'] = 'chart'
                                        elements_dict[k.split('__')[1]] = v
                                    elif 'action' in k:
                                        op_list.append(v)
                        # create dicts with operations info
                        for op in op_list:
                            op_dict = {}
                            op_dict['action'] = op
                            if op == 'count':
                                op_dict['param'] = 'label'
                            elif op == 'sort':
                                op_dict['param'] = 'another'
                            operations.append(op_dict)
                        elements_dict['operations'] = operations
                        dynamic_elements.append(elements_dict)

                    datastory_data['dynamic_elements'] = dynamic_elements
    update_json(file, general_data)
    datastory_name = datastory_title.lower().replace(" ", "_")
    return (datastory_name)

# access the home page


@app.route("/")
@app.route("/index.html")
def home():
    general_data = read_json('config.json')
    return render_template('index.html', general_data=general_data)

# github authentication


@app.route("/gitauth")
def gitauth():
    github_auth = "https://github.com/login/oauth/authorize"
    clientId = '6a49af44eaa2f9c3dfd0'
    scope = "&read:user"
    return redirect(github_auth+"?client_id="+clientId+scope)


@app.route("/oauth-callback")
def oauthcallback():
    code = request.args.get('code')
    res = github_sync.ask_user_permission(code)

    if res:
        userlogin, usermail, bearer_token = github_sync.get_user_login(res)
        is_valid_user = github_sync.get_github_users(userlogin)
        if is_valid_user == True:
            session["name"] = userlogin
            print("good chap, logged in as ", session["name"])
            return redirect(url_for('setup'))
    else:
        session["name"] = None
        print("bad boy's request to github oauth")
        return redirect(url_for('home'))

# signout


@app.route("/signout")
def signout():
    session["name"] = None
    return redirect(url_for('home'))

# access any datastory page


@app.route("/<string:section_name>/<string:datastory_name>")
def datastory(section_name, datastory_name):
    '''
    opens the config file, checks if datastory_name is inside data_sources and returns its page with the data(datastory_data)
    to be displayed.
    '''
    general_data = read_json('config.json')
    datastory_data = access_data_sources(
        section_name, datastory_name, 'config.json')
    if datastory_data:
        return render_template('datastory.html', datastory_data=datastory_data, general_data=general_data)
    else:
        return render_template('page-404.html')


@app.route("/setup", methods=['POST', 'GET'])
def setup():
    general_data = read_json('config.json')
    if request.method == 'GET':
        if session.get('name') is not None:
            if session['name']:
                template_data = []
                for item in general_data['templates']:
                    template_data.append(general_data['templates'][item])
                return render_template('setup.html', template_data=template_data, general_data=general_data)
        else:
            return render_template('asklogin.html', general_data=general_data)
    elif request.method == 'POST':
        if session.get('name') is not None:
            if session['name']:
                try:
                    # get data
                    form_data = request.form
                    template_mode = form_data['template_mode']
                    datastory_title = form_data['title']
                    datastory_endpoint = form_data['sparql_endpoint']
                    section_name = form_data['section_name']
                    color_code = ''
                    for item in general_data['templates']:
                        if general_data['templates'][item]['name'] == template_mode.lower():
                            color_code = general_data['templates'][item]['default_color']
                    # create new datastory instance
                    new_datastory = {}
                    new_datastory['sparql_endpoint'] = datastory_endpoint
                    new_datastory['template_mode'] = template_mode
                    new_datastory['title'] = datastory_title
                    new_datastory['color_code'] = color_code
                    new_datastory['section_name'] = section_name
                    # add to config file
                    clean_title = datastory_title.lower().replace(" ", "_")
                    clean_section = section_name.lower().replace(" ", "_")
                    if clean_section in general_data['data_sources']:
                        general_data['data_sources'][clean_section][clean_title] = new_datastory
                    else:
                        general_data['data_sources'][clean_section] = {}
                        general_data['data_sources'][clean_section][clean_title] = new_datastory

                    update_json('config.json', general_data)
                    general_data = read_json('config.json')

                    # upload the sections list
                    sections = set()
                    for story in general_data['data_sources'].values():
                        for el in story.values():
                            sections.add(el['section_name'])
                    general_data['sections'] = list(sections)
                    update_json('config.json', general_data)
                    general_data = read_json('config.json')

                    datastory_data = access_data_sources(
                        clean_section, clean_title, 'config.json')

                    # the correct template opens based on the name
                    return redirect(url_for("modify_datastory", section_name=clean_section, datastory_name=clean_title))
                except Exception as e:
                    return str(e)+'did not save to database'
    else:
        return 'something went wrong, try again'


@app.route("/send_data/<string:section_name>", methods=['POST', 'GET'])
def send_data(section_name):
    general_data = read_json('config.json')
    if request.method == 'POST':
        if session.get('name') is not None:
            if session['name']:
                try:
                    datastory_name = manage_datastory_data(
                        general_data, 'config.json', section_name)
                    return redirect(url_for('datastory', section_name=section_name, datastory_name=datastory_name))
                except:
                    return 'Something went wrong'


@app.route("/modify/<string:section_name>/<string:datastory_name>", methods=['POST', 'GET'])
def modify_datastory(section_name, datastory_name):
    datastory_data = access_data_sources(
        section_name, datastory_name, 'config.json')
    general_data = read_json('config.json')
    if request.method == 'GET':
        if session.get('name') is not None:
            if session['name']:
                return render_template('modify_datastory.html', datastory_data=datastory_data, general_data=general_data)
    elif request.method == 'POST':
        if session.get('name') is not None:
            if session['name']:
                if request.form['action'] == 'save':
                    try:
                        datastory_name = manage_datastory_data(
                            general_data, 'config.json', section_name)
                        return redirect(url_for('datastory', section_name=section_name, datastory_name=datastory_name))
                    except:
                        return 'Something went wrong'

                elif request.form['action'] == 'delete':
                    print(section_name, datastory_name, request.form)
                    datastory_title = request.form['title'].lower().replace(
                        " ", "_")
                    general_data['data_sources'][section_name].pop(
                        datastory_title, 'None')
                    update_json('config.json', general_data)
                    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
