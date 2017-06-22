Redmine Individual Project Migration Tool
=========================================

Project Rescue
--------------

With that tool, you can migrate individual project from Redmine 2.x / 3.2
from an instance to another with all their dependencies (issues, users, parent
projects, children projects, news, documents, attachments, custom fields etc..)

It is a script made in Python3 so make sure that it is already installed.

You need to make sure to run that script into a fresh new installation
of Redmine, but you can use it many times after the first usage without
causing any problems. Simply : **You need to run the first migration in a
fresh new installation of Redmine**.

Al the IDs and primary keys will be kept original. The new IDs will be bumped
from the setting value `relative.new_sequence` described in 'Configuration
procedure' section of this document.

The plugin is actually only compatible to migrate from MySQL to PostgreSQL
vice versa, but after a little few adjustments in the `lib/orm.py` file,
it should work like a charm with other kinds of databases.
Feel free to contribute that fix if you especially need this.


### License ###

This project is released under GNU GPLv3 license, don't hesitate to read
the `LICENSE` file for further informations.


### Installation procedure ###

You will need to install first `python3-pip` package
in order to run this command (that will install all dependencies) :

```bash
$ ./bootstrap
```

### Configuration procedure ###

Once you've installed the dependencies, you will need to copy the 
`config.yml.example` to `config.yml` and customize it accordingly to your needs:

You can completely remove the `src.ssh` and `dst.path` if you don't want
to migrate the attachments nor their files.

If `commit_at_each_entry` is set to true, each time an object is migrated,
it will be instantatly commited into the db, if set to false, the changes
will be commited only once everything migrated without any errors.

If `also_import_children_projects` is set to `true`, if an imported project
has childrens, they will be imported too, otherwise, they will not.

If `issue_relation_require_both_projects` is set to true, when there's relations
between issues of different projets, it will require that the both projects
are migrated in order to create the relation. This prevent from migrating
projects that you didn't wanted to.

Set your plugins to migrate their data. If you try to migrate data without
setting the according plugin (or you set a plugin that is not installed at all)
the migration process will likely to crash, but you have nothing to loose
from trying if you set `commit_at_each_entry = false` :

This tool is only compatible with those plugins for the moment, 

1. redmine_backlogs
2. redmine_issue_templates
3. redmine_mail_reminder


```yaml
src:
    type: mysql
    name: redmine_official
    host: localhost
    user: root
    pass: test
    ssh:
        host: 192.168.0.1
        user: test
        pass: test123
        path: /home/redmine/files/

dst:
    type: postgresql
    name: redmine_default
    host: 127.0.0.1
    user: postgres
    pass: test
    path: /var/lib/redmine/default/files/

commit_at_each_entry: false
also_import_children_projects: false
issue_relation_require_both_projects: true

relative:
    reference_table: issues
    new_sequence: 500000

plugins:
    - redmine_backlogs
    - redmine_issue_templates
    - redmine_mail_reminder
```

The `relative.reference_table` is the table that will be used as a reference
point to set the key indexes, and new_sequence will be the minimum ID possible
for new primary keys in order to avoid collisions when you run the script
multiple times while using the Redmine target instance in production.

For example, if you have 150 000 issues and 345 000 time entries.

The new issues sequence will be set to 500 000, and the new time entries
sequence will be set to `(345 000 / 150 000) * 500 000 = 1 150 000`.


### Usage procedure ###

Once everything is installed and configured, you now can launch the migration.

```bash
$ ./migrate.py [PROJECT_SLUG_IDENTIFIER]
```

### Contributing to this tool ###

We absolutely appreciate patches, feel free to contribute
directly on the GitHub project.

Repositories / Development website / Bug Tracker:

https://github.com/dctremblay/Project-Rescue

Do not hesitate to join us and post comments, suggestions,
questions and general feedback directly on the issues tracker.

Author : David Côté-Tremblay <imdc.technologies@gmail.com>
