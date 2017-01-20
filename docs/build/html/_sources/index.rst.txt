bigip-jb
========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Introduction:
=============

This script can be helpful in the daily manually administrative jobs on a BIG-IP and is therefore targeted to any BIG-IP administrator and consultant. Even if it is based on REST, it is not ment ot be used for any automation or orchestration integration, since it is purely targeted for the manual administration.

The main idea behind this project is, to create an easy way to reproduce the same configuration in a simple way by storing it in a json blob. Also it should be easy to create a json blob, without learning a new json scheme. Therefor I simply use the json output of the BIG-IP as basic for the json blob, so that it can be created simply by copy and paste.

The project based mainly on two python scripts:

``getjb.py``
  This is helping you to create a json blob with the configuration you would like to implement.
  But still it is possible to create your own json blob manually simply by copy paste.

``sendjb.py``
   This will send the finalized configuration from a json blob (.jb) file towards the targeted BIG-IP.

Limitations
-----------

Since the project based on the REST iControl API of the BIG-IP, the minimum required
version of the BIG-IP is v11.6.x.

I did this implementation based on v12.1.1 and I already recognized, that some additional work is necessary to get it running on v11.6.x as well. Therefore please use it on v12 only for now.

To your attention
-----------------

The usage of this scripts is on your own risk and it is up to you to make sure that the usage is not causing potential outages of your environment. Especially in a productive environment use this scripts with care and validate the function always in a test environment first.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
