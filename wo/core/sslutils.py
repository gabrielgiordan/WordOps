import csv
import os
import re

from wo.core.fileutils import WOFileUtils
from wo.core.logging import Log
from wo.core.shellexec import WOShellExec
from wo.core.variables import WOVariables


class SSL:

    def getexpirationdays(self, domain, returnonerror=False):
        # check if exist
        if not os.path.isfile('/etc/letsencrypt/live/{0}/cert.pem'
                              .format(domain)):
            Log.error(self, 'File Not Found: '
                      '/etc/letsencrypt/live/{0}/cert.pem'
                      .format(domain), False)
            if returnonerror:
                return -1
            Log.error(self, "Check the WordOps log for more details "
                      "`tail /var/log/wo/wordops.log` and please try again...")

        current_date = WOShellExec.cmd_exec_stdout(self, "date -d \"now\" +%s")
        expiration_date = WOShellExec.cmd_exec_stdout(
            self, "date -d \""
            "$(openssl x509 -in /etc/letsencrypt/live/"
            "{0}/cert.pem -text -noout | grep \"Not After\" "
            "| cut -c 25-)\" +%s"
            .format(domain))

        days_left = int((int(expiration_date) - int(current_date)) / 86400)
        if (days_left > 0):
            return days_left
        else:
            # return "Certificate Already Expired ! Please Renew soon."
            return -1

    def getexpirationdate(self, domain):
        # check if exist
        if not os.path.isfile('/etc/letsencrypt/live/{0}/cert.pem'
                              .format(domain)):
            Log.error(self, 'File Not Found: /etc/letsencrypt/'
                      'live/{0}/cert.pem'
                      .format(domain), False)
            Log.error(self, "Check the WordOps log for more details "
                      "`tail /var/log/wo/wordops.log` and please try again...")

        expiration_date = WOShellExec.cmd_exec_stdout(
            self, "date -d \"$(/usr/bin/openssl x509 -in "
            "/etc/letsencrypt/live/{0}/cert.pem -text -noout | grep "
            "\"Not After\" | cut -c 25-)\" "
            .format(domain))
        return expiration_date

    def siteurlhttps(self, domain):
        wo_site_webroot = ('/var/www/{0}'.format(domain))
        WOFileUtils.chdir(
            self, '{0}/htdocs/'.format(wo_site_webroot))
        if WOShellExec.cmd_exec(
                self, "{0} --allow-root core is-installed"
                .format(WOVariables.wo_wp_cli)):
            wo_siteurl = (
                WOShellExec.cmd_exec_stdout(
                    self, "{0} option get siteurl "
                    .format(WOVariables.wo_wpcli_path) +
                    "--allow-root --quiet"))
            test_url = re.split(":", wo_siteurl)
            if not (test_url[0] == 'https'):
                WOShellExec.cmd_exec(
                    self, "{0} option update siteurl "
                    "\'https://{1}\' --allow-root".format(
                        WOVariables.wo_wpcli_path, domain))
                WOShellExec.cmd_exec(
                    self, "{0} option update home "
                    "\'https://{1}\' --allow-root".format(
                        WOVariables.wo_wpcli_path, domain))
                WOShellExec.cmd_exec(
                    self, "{0} search-replace \'http://{0}\'"
                    "\'https://{0}\' --skip-columns=guid "
                    "--skip-tables=wp_users"
                    .format(domain))
                Log.info(
                    self, "Site address updated "
                    "successfully to https://{0}".format(domain))

    # check if a wildcard exist to secure a new subdomain

    def checkwildcardexist(self, wo_domain_name):

        wo_acme_exec = ("/etc/letsencrypt/acme.sh --config-home "
                        "'/etc/letsencrypt/config'")
        # export certificates list from acme.sh
        WOShellExec.cmd_exec(
            self, "{0} ".format(wo_acme_exec) +
            "--list --listraw > /var/lib/wo/cert.csv")

        # define new csv dialect
        csv.register_dialect('acmeconf', delimiter='|')
        # open file
        certfile = open('/var/lib/wo/cert.csv', mode='r', encoding='utf-8')
        reader = csv.reader(certfile, 'acmeconf')
        wo_wildcard_domain = ("*.{0}".format(wo_domain_name))
        for row in reader:
            if wo_wildcard_domain in row[2]:
                iswildcard = True
                break
            else:
                iswildcard = False
        certfile.close()

        return iswildcard
