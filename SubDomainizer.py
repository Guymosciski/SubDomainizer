#!/usr/bin/env python

#######################################
#    Author: Neeraj Sonaniya          #
#    Twitter: neeraj_sonaniya         #
#    Linkedin: neerajsonaniya         #
#    Facebook: neeraj.sonaniya        #
#    Medium: neerajedwards            #
#    Email: nsonaniya2010@gmail.com   #
#######################################


import termcolor
import base64
import json
import argparse
from bs4 import BeautifulSoup
import requests
import re
import socket
import ssl
import htmlmin
from urllib.parse import *
import tldextract
import sys
from multiprocessing.dummy import Pool as ThreadPool
from itertools import repeat
from collections import Counter
from math import log2
import urllib3
import queue
import glob
import os
import time
import warnings

parse = argparse.ArgumentParser()
parse.add_argument('-c', '--cookie',
                   help="Cookies which needs to be sent with request. User double quotes if have more than one.")
parse.add_argument('-cop', '--cloudop',
                   help="Enter the file name in which you want to save results of cloud services finding.")
parse.add_argument('-sop', '--secretop',
                   help="Enter the file name in which you want to save results of secrets found.") 
parse.add_argument(
    '-d', '--domain', help="Enter the top-level-domain to extract all the subdomain of that specific domain")
parse.add_argument(
    '-f', '--folder', help="Folder in which files needs to be scanned.")
parse.add_argument('-g', '--gitscan', help="Give this option if you wants to search for subdomain from github",
                   action='store_true')
parse.add_argument('-gt', '--gittoken', help="Finding subdomains from github")
parse.add_argument(
    '-k', '--nossl', help="Use it when SSL certiheadsficate is not verified.", action='store_true')
parse.add_argument('-l', '--listfile',
                   help="List file which contain list of URLs to be scanned for subdomains")
parse.add_argument('-o', '--output',
                   help="Enter the file name to which you want to save the results of subdomains found.")
parse.add_argument('-san', '--subject_alt_name', help="Get Subject Alternative Names, Options: 'all', 'same'")
parse.add_argument(
    '-u', '--url', help="Enter the URL in which you want to find (sub)domains.")

args = parse.parse_args()
url = args.url
listfile = args.listfile
cloudop = args.cloudop
secretop = args.secretop
gitToken = args.gittoken
isGit = args.gitscan
isSSL = args.nossl
folderName = args.folder
is_san = args.subject_alt_name

jsLinkList = list()
jsname = list()
finalset = set()
new_final_dict = dict()
secret_dict = dict()
git_data = dict()
cloudurlset = set()
ipv4list = set()
finallist = list()

if args.cookie:
    heads = {"Cookie": args.cookie,
             "User-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/70.0"}
else:
    heads = {"User-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/70.0"}


def argerror(urls, listfile):
    """

    This function will get all the files path (including filename) recursively, given root folder.

    Parameters
    ----------
    urls : str
        URL to scan for information.
    listfile: str
        Path of file which contains urls seperated by newline.
    """
    if (urls is None and listfile is None) or (urls is not None and listfile is not None):
        print("Atmost one of -u/--url or -l/--listfile or -f/--folder argument is required. Exiting...")
        sys.exit(1)
    else:
        pass


def gitArgError(gitToken, isGit):
    """

    This function will check if both -g and -gt arguments were provided or not, required for GitHub scanning.

    Parameters
    ----------
    gitToken : str
        Authtoken provided by github.
    isGit : None
        This argument will be used to tell the program to scan GitHub for information.
    """
    if (gitToken is None and isGit is not None) or (gitToken is not None and isGit is None):
        print("Either both '-g' and '-gt' arguments are required or none required. Exiting...")
        sys.exit(1)
    else:
        pass


def getRecursiveFolderData(rootfolder):
    """

    This function will get all the files path (including filename) recursively, given root folder.

    Parameters
    ----------
    rootfolder : str
        Root folder in which all files are present.

    Returns
    ----------
    dict
        dict of files path and their data.
    int
        total number of (only) files within the root folder.
    """
    folderData = dict()
    for filename in glob.iglob(rootfolder + '**/**', recursive=True):
        if os.path.isfile(filename):
            with open(filename, 'r') as file:
                try:
                    folderData[filename] = file.read()
                except UnicodeDecodeError:
                    pass
    return folderData, len(folderData)


def getUrlsFromFile():
    """

    Getting urls from file provided in input, file contains url seperated by newline.

    Returns
    ---------
    list
        It returns list of urls from file.
    """
    with open(args.listfile, 'rt') as f:
        urllst = f.readlines()
    urllst = [x.strip() for x in urllst if x != '']
    urllst = set(urllst)
    return urllst


class JsExtract:
    """
    This class contain the methods to get data from Internal (Inline) and External Javascript files (Present in <script> tag).

    Methods
    -------
    IntJsExtract(url, headers)
        It will get the data from Inline JS present within the page.
    -------
    ExtJsExtract(url, headers)
        It will get JS links present within source code of the page.
    -------
    SaveExtJsContent(js = JavascriptFileURL)
        This module will get the data from JS URL provided and add data in master list (finallist).
    """

    def IntJsExtract(self, url, heads):
        """

        Parameters
        ----------
        url : str
            URL of the page from which data needs to be extracted.
            Note: This is the url of the page given as user input.
        heads : dict
            Headers needed to make request, given URL.

        Raises
        ----------
        UnicodeDecodeError
            Raise an error if the endcoding found in the page is unkown.
        """

        if url.startswith('http://') or url.startswith('https://'):
            if isSSL:
                req = requests.get(url, headers=heads, verify=False)
            else:
                req = requests.get(url, headers=heads)
        else:
            if isSSL:
                req = requests.get(
                    'http://' + url, headers=heads, verify=False)
            else:
                req = requests.get('http://' + url, headers=heads)

        print(termcolor.colored("Searching for Inline Javascripts...",
                                color='yellow', attrs=['bold']))

        try:
            html = unquote(req.content.decode('unicode-escape'))
            minhtml = htmlmin.minify(html, remove_empty_space=True)
            minhtml = minhtml.replace('\n', '')
            finallist.append(minhtml)
            new_final_dict["Inline"] = minhtml
            print(termcolor.colored(
                "Successfully got all the Inline Scripts.", color='blue', attrs=['bold']))
        except UnicodeDecodeError:
            print(termcolor.colored("Decoding error...",
                                    color='red', attrs=['bold']))

    def ExtJsExtract(self, url, heads):
        """

        Parameters
        ----------
        url : str
            URL of the page from which data needs to be extracted.
            Note: This is the url of the page given as user input.
        heads : dict
            Headers needed to make request, given URL.

        Raises
        ----------
        UnicodeDecodeError
            Raise an error if the endcoding found in the page is unkown.
        """
        # domain = urlparse(url).netloc

        print(termcolor.colored(
            "Searching for External Javascript links in page...", color='yellow', attrs=['bold']))
        if url.startswith('http://') or url.startswith('https://'):
            if isSSL:
                req = requests.get(url, headers=heads, verify=False)
            else:
                req = requests.get(url, headers=heads)
        else:
            if isSSL:
                req = requests.get(
                    'http://' + url, headers=heads, verify=False)
            else:
                req = requests.get('http://' + url, headers=heads)
        try:
            html = unquote(req.content.decode('unicode-escape'))
            soup = BeautifulSoup(html, features='html.parser')

            for link in soup.find_all('script'):
                if link.get('src'):
                    text = urljoin(url, link.get('src'))
                    jsLinkList.append(text)
                    # jsLinkList.append(text + link.get('src').strip())
            print(termcolor.colored(
                "Successfully got all the external js links.", color='blue', attrs=['bold']))
        except UnicodeDecodeError:
            print("Decoding error, Exiting...")
            sys.exit(1)

    def SaveExtJsContent(self, js):
        """

        Parameters
        ----------
        js : str
            Link to the URL of external Javascript file.
        """
        try:
            if isSSL:
                content = unquote(requests.get(
                    js, verify=False, headers=heads).content.decode('utf-8'))
                finallist.append(content)
                new_final_dict[str(js)] = content
            else:
                content = unquote(requests.get(js, headers=heads).content.decode('utf-8'))
                finallist.append(content)
                new_final_dict[str(js)] = content
        except:
            pass


def logo():
    """

    Prints the logo

    Returns
    ---------
    str
        Return the logo string.
    """
    return r"""
      _____       _     _____                        _       _              
     / ____|     | |   |  __ \                      (_)     (_)             
    | (___  _   _| |__ | |  | | ___  _ __ ___   __ _ _ _ __  _ _______ _ __ 
     \___ \| | | | '_ \| |  | |/ _ \| '_ ` _ \ / _` | | '_ \| |_  / _ \ '__|
     ____) | |_| | |_) | |__| | (_) | | | | | | (_| | | | | | |/ /  __/ |   
    |_____/ \__,_|_.__/|_____/ \___/|_| |_| |_|\__,_|_|_| |_|_/___\___|_|Version 2.0                                                                                                                                       
Find interesting Subdomains and secrets hidden in page, folder, External Javascripts and GitHub 
"""


def entropy(s):
    """

    This function find the entropy given the string given by the formula:
    https://www.reddit.com/r/dailyprogrammer/comments/4fc896/20160418_challenge_263_easy_calculating_shannon/

    Parameters
    -------
    s: str
        String of which we have to find shannon entropy

    Returns
    --------
    int
        integer which will represent the randomness of the string, higher value will be high randomness.
    """
    return -sum(i / len(s) * log2(i / len(s)) for i in Counter(s).values())


def getDomain(url):
    """

    This function will get top level domain from given URL.

    Parameters
    -------
    url: str
        Original URL provided in the argument.

    Returns
    --------
    str
        top level domain will be returned.
    """
    if urlparse(url).netloc != '':
        finalset.add(urlparse(url).netloc)
    ext = tldextract.extract(str(url))
    return ext.registered_domain


def tldExt(name):
    return tldextract.extract(name).registered_domain


def tldSorting(subdomainList):
    """

    This function will sort all the items within the list in dictionary order.

    Parameters
    -------
    subdomainList: list
        List of subdomains found from content.

    Returns
    --------
    list
        a list of subdomains.
    """

    localsortedlist = list()
    finallist = list()
    for item in subdomainList:
        Reverseddomain = ".".join(str(item).split('.')[::-1])
        localsortedlist.append(Reverseddomain)

    sortedlist = sorted(localsortedlist)

    for item in sortedlist:
        reReverseddomain = ".".join(str(item).split('.')[::-1])
        finallist.append(reReverseddomain)

    return finallist


def PreCompiledRegexSecret():
    """

    This function will create list of precompiled regex object to find secret (high entropy strings) within the content.

    Returns
    --------
    list
        a list of precompiled regex objects.
    """
    seclst = ['secret', 'secret_key', 'token', 'secret_token', 'auth_token', 'access_token', 'username', 'password',
              'aws_access_key_id', 'aws_secret_access_key', 'secretkey', 'authtoken', 'accesstoken', 'access-token',
              'authkey', 'client_secret', 'key', 'email', 'HEROKU_API_KEY', 'SF_USERNAME', 'PT_TOKEN',
              'id_dsa',
              'clientsecret', 'client-secret', 'encryption-key', 'pass', 'encryption_key', 'encryptionkey', 'secretkey',
              'secret-key', 'bearer', 'JEKYLL_GITHUB_TOKEN', 'HOMEBREW_GITHUB_API_TOKEN',
              'api_key', 'api_secret_key', 'api-key', 'private_key', 'client_key', 'client_id', 'sshkey', 'ssh_key',
              'ssh-key', 'privatekey', 'DB_USERNAME', 'oauth_token', 'irc_pass', 'dbpasswd', 'xoxa-2', 'xoxr'
                                                                                                       'private-key',
              'private_key', 'consumer_key', 'consumer_secret', 'access_token_secret', 'SLACK_BOT_TOKEN',
              'slack_api_token', 'api_token', 'ConsumerKey', 'ConsumerSecret', 'SESSION_TOKEN', 'session_key',
              'session_secret', 'slack_token', 'slack_secret_token', 'bot_access_token']
    equal = ['=', ':', '=>', '=:']

    return re.compile(r'(["\']?[\\w\-]*(?:' + '|'.join(seclst) + ')[\\w\\-]*[\\s]*["\']?[\\s]*(?:' + '|'.join(
        equal) + ')[\\s]*["\']?([\\w\\-/~!@#$%^*+.]+=*)["\']?)',
                      re.MULTILINE | re.IGNORECASE)


def PreCompiledRegexCloud():
    """

    This will create list of precompiled regex object to find cloud URLs within the content.

    Returns
    --------
    list
        a list of precompiled regex objects.
    """
    cfreg = re.compile(r'([\w]+\.cloudfront\.net)',
                       re.MULTILINE | re.IGNORECASE)
    gbureg = re.compile(r'([\w\-.]+\.appspot\.com)',
                        re.MULTILINE | re.IGNORECASE)
    s3bucketreg = re.compile(
        r'([\w\-.]*s3[\w\-.]*\.?amazonaws\.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    doreg = re.compile(
        r'([\w\-.]*\.?digitaloceanspaces\.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    gsreg1 = re.compile(
        r'(storage\.cloud\.google\.com/[\w\-.]+)', re.MULTILINE | re.IGNORECASE)
    gsreg2 = re.compile(
        r'([\w\-.]*\.?storage.googleapis.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    gsreg3 = re.compile(
        r'([\w\-.]*\.?storage-download.googleapis.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    gsreg4 = re.compile(
        r'([\w\-.]*\.?content-storage-upload.googleapis.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    gsreg5 = re.compile(
        r'([\w\-.]*\.?content-storage-download.googleapis.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    azureg1 = re.compile(
        r'([\w\-.]*\.?1drv\.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    azureg2 = re.compile(
        r'(onedrive.live.com/[\w.\-]+)', re.MULTILINE | re.IGNORECASE)
    azureg3 = re.compile(
        r'([\w\-.]*\.?blob\.core\.windows\.net/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    rackcdnreg = re.compile(
        r'([\w\-.]*\.?rackcdn.com/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    dreamhostreg1 = re.compile(
        r'([\w\-.]*\.?objects\.cdn\.dream\.io/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    dreamhostreg2 = re.compile(
        r'([\w\-.]*\.?objects-us-west-1.dream.io/?[\w\-.]*)', re.MULTILINE | re.IGNORECASE)
    firebase = re.compile(r'([\w\-.]+\.firebaseio\.com)',
                          re.MULTILINE | re.IGNORECASE)

    cloudlist = [cfreg, s3bucketreg, doreg, gsreg1, gsreg2, gsreg3, gsreg4, gsreg5,
                 azureg1, azureg2, azureg3, rackcdnreg, dreamhostreg1, dreamhostreg2, firebase, gbureg]

    return cloudlist


def PreCompiledRegexDomain(url):
    """

    Precompiled regex to get domain from the URL.

    Parameters
    --------
    url: str
        Original URL from user provided input (URL argument).
    """
    regex = re.compile(r'([a-zA-Z0-9][a-zA-Z0-9\-.]*[a-zA-Z0-9]\.' +
                       str(getDomain(str(url))) + ')', re.IGNORECASE)
    return regex


def PreCompiledRegexIP():
    """

    Precompiled regex to find IP version 4 address from the content.

    Returns
    ---------
    object
        Regex compiled object
    """
    ipv4reg = re.compile(r"""(([2][5][0-5]\\\\.)|([2][0-4][0-9]\\\\.)|([0-1]?[0-9]?[0-9]\\\\.)){3}"""
                         + """(([2][5][0-5])|([2][0-4][0-9])|([0-1]?[0-9]?[0-9]))""")
    return ipv4reg


def getInfoFromData(item_url, item_values, cloudlist, p, regex, ipv4reg, url):
    """

    This function is used to call other functions to find secrets, cloud URLs etc.

    Parameters
    --------
    file: list
        List contains all the content from different source to find secrets, cloud URLs etc.
    cloudlist: object
        Precompiled regex object to find cloud URLs.
    p: object
        Precompiled regex object to find secret (high entropy strings) from content in the list.
    regex: object
        Precompiled regex object to find subdomains for a given domain.
    ipv4reg: object
        Precompiled regex object to find IP version 4 addresses within content.
    url: str
        Original URL from user provided input (URL argument).
    """
    item_values = str(item_values).replace('\n', ' ')

    # cloud services
    for x in cloudlist:
        for item in x.findall(str(item_values)):
            cloudurlset.add(item)

    matches = p.finditer(str(item_values))
    for matchNum, match in enumerate(matches):
        if entropy(match.group(2)) > 3.5:
            if item_url in secret_dict:
                secret_dict[item_url].append(str(match.group()))
            else:
                secret_dict[item_url] = [str(match.group())]

    # try:
    #     st = file.split()
    #     for i in st:
    #         match = ipv4reg.search(i)
    #         if match:
    #             ipv4list.add(match.group())
    # except:
    #     pass

    # for subdomains
    for subdomain in regex.findall(str(item_values)):
        finalset.add(subdomain.lower())

    # given domain regex
    if args.domain:
        domainreg = re.compile(
            r'([a-zA-Z0-9][0-9a-zA-Z\-.]*[a-zA-Z0-9]\.' + args.domain + ')', re.IGNORECASE)
        for subdomain in domainreg.findall(str(item_values)):
            finalset.add(subdomain)


def getUrlsFromData(gitToken, domain):
    """

    This function will get URLs which contains data related to domain from GitHub API.

    Parameters
    ----------
    gitToken: str
        AuthToken provided GitHub.
    domain: str
        Domain from the url provided in argument by user.

    Returns
    ----------
    list
        list of urls from github.
    """

    datas = list()
    contentApiURLs = set()

    datas.append(requests.get(
        'https://api.github.com/search/code?q="' + domain +
        '"&access_token=' + gitToken + '&per_page=100&sort=indexed',
        verify=False, headers=heads).content.decode('utf-8'))
    datas.append(requests.get(
        'https://api.github.com/search/code?q="' + domain +
        '"&access_token=' + gitToken + '&per_page=100',
        verify=False, headers=heads).content.decode('utf-8'))

    for data in datas:
        data = json.loads(data)
        if 'items' in data:
            for item in data['items']:
                for key, value in item.items():
                    if key == 'url':
                        contentApiURLs.add(value)

    return contentApiURLs


def getGithubData(item):
    """

    This function will get data for a given GitHub URL.

    Parameters
    ----------
    item: str
        URL pointing to github data related to the given domain.

    """
    item = item + '&access_token=' + gitToken
    try:
        apiUrlContent = requests.get(
            item, verify=False).content.decode('utf-8')
        jsonData = json.loads(apiUrlContent)
        _data = base64.b64decode(jsonData['content'])
        _data = unquote(unquote(str(_data, 'utf-8')))
        final_data = str(_data.replace('\n', ' '))
        git_data[jsonData.get('html_url').split("?ref=")[0]] = final_data

    except requests.ConnectionError:
        pass


def subextractor(cloudlist, p, regex, ipv4reg, url):
    """

    This function is used to call other functions to find secrets, cloud URLs etc.

    Parameters
    --------
    cloudlist: object
        Precompiled regex object to find cloud URLs.
    p: object
        Precompiled regex object to find secret (high entropy strings) from content in the list.
    regex: object
        Precompiled regex object to find subdomains for a given domain.
    ipv4reg: object
        Precompiled regex object to find IP version 4 addresses within content.
    url: str
        Original URL from user provided input (URL argument).
    """
    jsfile = JsExtract()
    jsfile.IntJsExtract(url, heads)
    jsfile.ExtJsExtract(url, heads)
    jsthread = ThreadPool(300)
    jsthread.map(jsfile.SaveExtJsContent, jsLinkList)
    jsthread.close()
    jsthread.join()
    print(termcolor.colored("Finding secrets, cloud URLs, subdomains in all Javascript files...",
                            color='yellow',
                            attrs=['bold']))
    threads = ThreadPool(300)
    threads.starmap(getInfoFromData,
                    zip(new_final_dict.keys(), new_final_dict.values(), repeat(cloudlist), repeat(p), repeat(regex),
                        repeat(ipv4reg), repeat(url)))
    threads.close()
    threads.join()
    print(termcolor.colored("Searching completed...",
                            color='blue', attrs=['bold']))
    finallist.clear()


def savedata():
    """

    This function will put data in output file if given.

    """

    # for item in tldSorting(finalset):
    #     print(termcolor.colored(item, color='green', attrs=['bold']))
    # if ipv4list:
    #     print(termcolor.colored("\nGot Some IPv4 addresses:\n",
    #                             color='blue', attrs=['bold']))
    #     for ip in ipv4list:
    #         if socket.getfqdn(ip) != ip:
    #             print(termcolor.colored(ip + ' - ' + socket.getfqdn(ip),
    #                                     color='green', attrs=['bold']))

    print(termcolor.colored(
        "\nWriting all the subdomains to given file...\n", color='yellow', attrs=['bold']))
    with open(args.output, 'w+') as f:
        for item in tldSorting(finalset):
            f.write(item + '\n')
    print(termcolor.colored("\nWriting Done..\n",
                            color='yellow', attrs=['bold']))


def savecloudresults():
    """
    This function will save cloud URL's data into the given file.
    """
    with open(cloudop, 'w+') as f:
        for item in cloudurlset:
            f.write(item + '\n')

def savesecretsresults():
    """
    This function will save secret data into the given file.
    """
    with open(secretop, 'w+') as f:
        for location, secretlst in secret_dict.items():
            for secret in secretlst:
                f.write(secret + ' | ' + location + '\n')


def printlogo():
    """
    Print the logo returned by logo() function.

    Returns
    ---------
    object
        Termcolor object to print colored logo on CLI screen.
    """
    return termcolor.colored(logo(), color='red', attrs=['bold'])


if __name__ == "__main__":

    domainSet = set()
    compiledRegexCloud = PreCompiledRegexCloud()
    compiledRegexSecretList = PreCompiledRegexSecret()
    compiledRegexIP = PreCompiledRegexIP()

    try:
        print(printlogo())

        # disable unicode-esacpe for string - deprecation warning.
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # disable insecure ssl warning.
        if isSSL:
            print(termcolor.colored("Disabled SSL Certificate Checking...",
                                    color='green',
                                    attrs=['bold']))

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # checking if only folder needs to be scanned.
        if folderName and not url and not listfile:

            # if isGit:
            #     gitArgError(gitToken, isGit)

            print(termcolor.colored("Getting data from folder recursively...", color='yellow',
                                    attrs=['bold']))
            if not os.path.isfile(folderName):
                folderData, totalLength = getRecursiveFolderData(folderName)
            else:
                folderData = dict()
                totalLength = 1
                file_name = folderName
                with open(file_name, 'rt') as file:
                    try:
                        folderData[file_name] = file.read()
                    except UnicodeDecodeError:
                        pass

            print(termcolor.colored(
                "\nTotal files to scan: " + str(totalLength) + '\n', color='red', attrs=['bold']))

            time.sleep(0.5)
            print(termcolor.colored("Finding secrets in files, Please wait...", color='blue',
                                    attrs=['bold']))
            for path, data in folderData.items():

                for cloud in compiledRegexCloud:
                    for item in cloud.findall(str(data.replace('\n', ' '))):
                        cloudurlset.add(item)

                matches = compiledRegexSecretList.finditer(
                    str(data.replace('\n', ' ')))
                for matchNum, match in enumerate(matches):
                    if entropy(match.group(2)) > 3.5:
                        # secretList.add(match.group())
                        _path = os.path.normpath(os.path.join(os.getcwd(), path))
                        if _path in secret_dict:
                            secret_dict[_path].append(str(match.group()))
                        else:
                            secret_dict[_path] = [str(match.group())]

                if args.domain:
                    compiledRegexDomain = PreCompiledRegexDomain(args.domain)
                    for subdomain in compiledRegexDomain.findall(str(data.replace('\n', ' '))):
                        finalset.add(subdomain)

            # if isGit and args.domain:
            #     compiledRegexDomain = PreCompiledRegexDomain(args.domain)
            #     domain = str(getDomain(args.domain))
            #     print(termcolor.colored('Finding Subdomains and secrets from Github..Please wait...',
            #                             color='yellow',
            #                             attrs=['bold']))
            #     print(termcolor.colored(
            #         'Searching in github for : ' + termcolor.colored(domain, color='green',
            #                                                          attrs=['bold']), color='blue',
            #         attrs=['bold']))

            #     gitThread = ThreadPool(200)
            #     contentApiURLs = getUrlsFromData(gitToken, str(domain))
            #     gitHublist = gitThread.map(getGithubData, contentApiURLs)
            #     gitContentThread = ThreadPool(200)

            # for ghitem in gitHublist: gitContentThread.starmap(getInfoFromData, zip(ghitem,
            # repeat(compiledRegexCloud), repeat( compiledRegexSecretList), repeat(compiledRegexDomain),
            # repeat( compiledRegexIP), repeat(domain))) print( termcolor.colored('Completed finding from github...',
            # color='blue', attrs=['bold'])) else: print( termcolor.colored('Not scanned from github as domain not
            # given, use \'-d\' to give domain...', color='red', attrs=['bold']))

        else:
            argerror(url, listfile)
            if isGit:
                gitArgError(gitToken, isGit)
            if listfile:
                urllist = getUrlsFromFile()
                if urllist:
                    for i in urllist:
                        compiledRegexDomain = PreCompiledRegexDomain(i)
                        domainSet.add(str(getDomain(str(i))))
                        print(termcolor.colored("Extracting data from internal and external js for url:", color='blue',
                                                attrs=['bold']))
                        print(termcolor.colored(
                            i, color='red', attrs=['bold']))
                        try:
                            try:
                                subextractor(compiledRegexCloud, compiledRegexSecretList, compiledRegexDomain,
                                             compiledRegexIP, i)
                            except requests.exceptions.ConnectionError:
                                print(
                                    'An error occured while fetching URL, Might be URL is wrong, Please check!')
                        except requests.exceptions.InvalidSchema:
                            print("Invalid Schema Provided!")
                            sys.exit(1)
            else:
                try:
                    try:
                        compiledRegexDomain = PreCompiledRegexDomain(url)
                        domainSet.add(str(getDomain(str(url))))
                        subextractor(compiledRegexCloud, compiledRegexSecretList,
                                     compiledRegexDomain, compiledRegexIP, url)
                    except requests.exceptions.ConnectionError:
                        print(
                            termcolor.colored(
                                'An error occured while fetching URL, one or more of following are possibilities:'
                                '\n1. Might be server is down.\n2. SSL certificate issue.\n3. Domain does not exist. '
                                '\nPlease check properly or try \'-k\' option, to disable SSL certificate '
                                'verification.',
                                color='yellow', attrs=['bold']))
                        sys.exit(1)
                except requests.exceptions.InvalidSchema:
                    print("Invalid Schema Provided!")
                    sys.exit(1)

            if gitToken and isGit:
                for item in domainSet:
                    compiledRegexDomain = PreCompiledRegexDomain(item)
                    print(
                        termcolor.colored('Finding Subdomains and secrets from Github..Please wait...', color='yellow',
                                          attrs=['bold']))
                    print(termcolor.colored(
                        'Searching in github for : ' + termcolor.colored(item, color='green', attrs=['bold']),
                        color='blue',
                        attrs=['bold']))

                    gitThread = ThreadPool(200)
                    contentApiURLs = getUrlsFromData(gitToken, str(item))
                    gitThread.map(getGithubData, contentApiURLs)
                    gitContentThread = ThreadPool(200)

                    try:
                        gitContentThread.starmap(getInfoFromData,
                                                 zip(git_data.keys(), git_data.values(), repeat(compiledRegexCloud),
                                                     repeat(compiledRegexSecretList),
                                                     repeat(compiledRegexDomain), repeat(compiledRegexIP),
                                                     repeat(item)))
                    except:
                        pass
                    print(termcolor.colored(
                        'Completed finding from github...', color='blue', attrs=['bold']))


    except KeyboardInterrupt:
        print(termcolor.colored("\nKeyboard Interrupt. Exiting...\n",
                                color='red', attrs=['bold']))
        sys.exit(1)
    except FileNotFoundError:
        print(
            termcolor.colored("\nFile Not found, Please check filename. Exiting...\n", color='yellow', attrs=['bold']))
        sys.exit(1)

    print(termcolor.colored("Got all the important, printing and/or saving...\n", color='blue',
                            attrs=['bold']))
    print(termcolor.colored('_' * 22 + 'Start of Results' +
                            '_' * 22, color='white', attrs=['bold']))

    if args.output:
        savedata()

    if cloudop:
        print(
            termcolor.colored("\nWriting all the cloud services URL's to given file...", color='yellow',
                                attrs=['bold']))
        savecloudresults()
        print(
            termcolor.colored("Written cloud services URL's in file: ", color='red',
                              attrs=['bold']) + cloudop)

    if secretop:
        print(termcolor.colored("\nWriting all the secrets to given file...", color='yellow', attrs=['bold']))
        savesecretsresults()
        print(termcolor.colored("Written secrets in file: ", color='red',
                                attrs=['bold']) + secretop)
    
    print(termcolor.colored('_' * 60, color='white', attrs=['bold']))


    if finalset:
        print(termcolor.colored("\nGot some subdomains...", color='yellow',
                                attrs=['bold']))
        print(termcolor.colored('Total Subdomains: ' +
                                str(len(finalset)), color='red', attrs=['bold']))
        for item in tldSorting(finalset):
            print(termcolor.colored(
                item, color='green', attrs=['bold']))

    if cloudurlset:
        print(termcolor.colored('_' * 60, color='white', attrs=['bold']))
        print(termcolor.colored("\nSome cloud services urls are found...", color='yellow',
                                attrs=['bold']))
        print(termcolor.colored('Total Cloud URLs: ' +
                                str(len(cloudurlset)), color='red', attrs=['bold']))
        for item in cloudurlset:
            print(termcolor.colored(item, color='green', attrs=['bold']))

    if secret_dict:
        print(termcolor.colored('_' * 60, color='white', attrs=['bold']))
        print(termcolor.colored("\nFound some secrets(might be false positive)...", color='yellow',
                                attrs=['bold']))
                                
        print(termcolor.colored('Total Possible Secrets: ' +
                                str(sum(len(sec_lst) for sec_lst in secret_dict.values())), color='red',
                                attrs=['bold']))
        for file_url, secrets in secret_dict.items():
            for secret in set(secrets):
                print(termcolor.colored(secret, color='green', attrs=['bold']),
                      termcolor.colored("| " + file_url, color='yellow', attrs=['bold']))

    if is_san in ("same", "all") and url and not folderName:
        print(termcolor.colored('_' * 60, color='white', attrs=['bold']))
        print(termcolor.colored("\nFinding additional subdomains using Subject Alternative Names(SANs)...\n",
                                color='yellow',
                                attrs=['bold']))
        nothing_found_flag = True
        context = ssl.create_default_context()
        context.check_hostname = False

        socket.setdefaulttimeout(5)

        q = queue.Queue()
        printed = set()
        completed = set()

        finalset.add(tldExt(url))

        for host in finalset:
            tld = getDomain(host)
            q.put(host)
            while not q.empty():
                try:
                    hostname = q.get()
                    if is_san == "same":
                        if hostname not in printed and hostname not in finalset and hostname.endswith(tld):
                            print(termcolor.colored(hostname, color='green', attrs=['bold']))
                            nothing_found_flag = False
                            printed.add(hostname)
                    elif is_san == "all":
                        if hostname not in printed and hostname not in finalset:
                            print(termcolor.colored(hostname, color='green', attrs=['bold']))
                            nothing_found_flag = False
                            printed.add(hostname)

                    if hostname not in completed:
                        completed.add(hostname)
                        with socket.create_connection((hostname, 443)) as sock:
                            with context.wrap_socket(sock, server_hostname=hostname, ) as ssock:
                                for (k, v) in ssock.getpeercert()['subjectAltName']:
                                    if v not in q.queue and v.startswith("*.") and v.lstrip('*.') not in finalset:
                                        q.put(v.lstrip('*.'))
                                    elif v not in q.queue and v not in finalset:
                                        q.put(v.lstrip('*.'))
                except (socket.gaierror, socket.timeout, ssl.SSLCertVerificationError, ConnectionRefusedError,
                        ssl.SSLError,
                        OSError):
                    pass
                except KeyboardInterrupt:
                    print(termcolor.colored("\nKeyboard Interrupt. Exiting...\n",
                                            color='red', attrs=['bold']))
                    sys.exit(1)

        if nothing_found_flag:
            print(termcolor.colored("No SANs found.", color='green', attrs=['bold']))

    print(termcolor.colored('\n' + '_' * 23 + 'End of Results' +
                            '_' * 23 + '\n', color='white', attrs=['bold']))
