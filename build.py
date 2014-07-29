# This python script builds Privly applications so they
# can share a common user interface and (eventually)
# support localization. If you are building
# a new application, you will probably want to copy
# an existing application folder, e.g. PlainPost,
# to a new directory and work there. When you are
# wanting to ship the application, we will work to
# integrate it with this build system.
#
# Prerequisites for running this script include
# BeautifulSoup and Jinja2. You can install
# them both with:
# `sudo easy_install beautifulsoup4 jinja2`
#
# This assumes you have python-setuptools:
# `sudo apt-get install python-setuptools`
#
# This script uses the jinja2 templating system:
# http://jinja.pocoo.org/docs/
#
# We prefer readability over minified apps. BeautifulSoup
# properly formats the HTML so it is nested and readable.
# http://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-beautiful-soup
#
# You can run the script from the privly-applications directory:
# `python build.py`
#
# This templating system is a starting point, but is 
# not fully featured. You can currently add new
# applications by adding to the "to_build" object
# below.
#
# Note: if you are building for a platform that has platform
# specific code

from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup as bs
import os
import json
import re
import argparse # Parsing arguments

def make_readable(html):
  """
  Make the rendered HTML formatting readable
  @param {string} html The HTML that we need to make readable.
  """
  soup = bs(html)
  prettyHTML = soup.prettify().encode("utf8")
  
  # Beautiful soup breaks textarea formatting
  # since it adds extra whitespace. If you use "pre"
  # tags, you should be warry of the same problem
  return re.sub(r'[\ \n]{2,}</textarea>',
               "</textarea>",
               prettyHTML)

def render(outfile_path, subtemplate_path, subtemplate_dict):
  """
  Render the templates to html.
  @param {string} outfile The relative path to the file which we are rendering
    to.
  @param {string} subtemplate_path The relative path to the file of the subtemplate
    to be rendered.
  @param {dictionary} subtemplate_dict The variables required by the subtemplate.
  """
  f = open(outfile_path, 'w')
  subtemplate = env.get_template(subtemplate_path)
  html = subtemplate.render(subtemplate_dict)
  prettyHTML = make_readable(html)
  f.write(prettyHTML)
  f.close()

def is_build_target(template):
  """
  Determines whether the build target is currently active.
  @param {dictionary} template The dictionary of the object to build.
  """
  return "platforms" not in template or args.platform in template["platforms"]

def get_link_creation_apps():
  """
  Gets a list of the apps that will be included in the top navigation
  for generating new links
  """
  creation_apps = []

  for dirname, dirnames, filenames in os.walk('.'):
    if "manifest.json" in filenames:
      f = open(dirname + "/manifest.json", 'r')
      template_list = json.load(f)
      f.close()
      for template in template_list:
        if is_build_target(template):
          if "nav" in template.keys() and template["nav"] == "new":
            creation_apps.append(template["subtemplate_dict"]["name"])

  # Hack to maintain current app order
  creation_apps.reverse()
  return creation_apps

if __name__ == "__main__":
  
  # Change the current working directory to the directory of the build script
  abspath = os.path.abspath(__file__)
  dname = os.path.dirname(abspath)
  os.chdir(dname)

  # Specify the potential build targets
  platforms = ['web', 'chrome']

  # Parse Arguments
  parser = argparse.ArgumentParser(description='Declare platform build target.')
  parser.add_argument('-p', '--platform', metavar='p', type=str,
                     help='The platform you are building for',
                     required=False,
                     default='web',
                     choices=platforms)
  args = parser.parse_args()
  
  # Templates are all referenced relative to the current
  # working directory
  env = Environment(loader=FileSystemLoader('.'))
  
  # Quick hack to make apps aware of each other in the templating.
  packages = {"new": get_link_creation_apps()}
  
  # The build list for applications is and array of objects:
  # {
  #   "subtemplate_path": The path to the subtemplate we are building.
  #   "outfile_path": The path to where we want to write the output file.
  #   "subtemplate_dict": The variables to pass into the subtemplate.
  # }
  #
  # Eventually it would be good to move this config into a manifest file
  # included in the directory.
  
  print("################################################")
  print("Targeting the *{0}* platform".format(args.platform))
  print("################################################")

  # Build the templates.
  print("Building...")

  # Find all the manifest files
  for dirname, dirnames, filenames in os.walk('.'):
    if "manifest.json" in filenames:
      f = open(dirname + "/manifest.json", 'r')
      template_list = json.load(f)
      f.close()

      for template in template_list:

        # Don't build the app if a platform is specified and it is not the
        # currently targeted platform
        if not is_build_target(template):
          continue

        template["subtemplate_dict"].update({"args": args, "packages": packages})
        print("{0}'s {1} action to {2}".format(
          template["subtemplate_dict"]["name"],
          template["subtemplate_dict"]["action"],
          template["outfile_path"]))
        render(template["outfile_path"], template["subtemplate_path"],
               template["subtemplate_dict"])

print("################################################")
print("Build complete.  You can now view the generated applications in their folders.")
