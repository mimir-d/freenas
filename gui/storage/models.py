#+
# Copyright 2010 iXsystems
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# $FreeBSD$
#####################################################################

from django.db import models
from django.utils.translation import ugettext_lazy as _
from freenasUI.choices import *
from freenasUI.middleware.notifier import notifier
from freeadmin.models import Model
from os import statvfs
from freenasUI.common import humanize_number_si

class Volume(Model):
    vol_name = models.CharField(
            unique=True,
            max_length=120, 
            verbose_name="Name"
            )
    vol_fstype = models.CharField(
            max_length=120, 
            choices=VolumeType_Choices, 
            verbose_name="File System Type", 
            )
    class Meta:
        verbose_name = "Volume"
    def delete(self):
        notifier().destroy("volume", self.id)
        notifier().restart("collectd")
        # The framework would cascade delete all database items
        # referencing this volume.
        super(Volume, self).delete()
	# Refresh the fstab
        notifier().reload("disk")
    def __unicode__(self):
        return "%s (%s)" % (self.vol_name, self.vol_fstype)

class DiskGroup(Model):
    group_name = models.CharField(
            unique=True,
            max_length=120, 
            verbose_name="Name"
            )
    group_type = models.CharField(
            max_length=120, 
            choices=(), 
            verbose_name="Type", 
            )
    group_volume = models.ForeignKey(
            Volume,
            verbose_name="Volume",
            help_text="Volume this group belongs to",
            )
    def __unicode__(self):
        return "%s (%s)" % (self.group_name, self.group_type)

class Disk(Model):
    disk_name = models.CharField(
            unique=True,
            max_length=120, 
            verbose_name="Name"
            )
    disk_disks = models.CharField(
            max_length=120, 
            verbose_name="Disks"
            )
    disk_description = models.CharField(
            max_length=120, 
            verbose_name="Description", 
            blank=True
            )
    disk_transfermode = models.CharField(
            max_length=120, 
            choices=TRANSFERMODE_CHOICES, 
            default="Auto", 
            verbose_name="Transfer Mode"
            )
    disk_hddstandby = models.CharField(
            max_length=120, 
            choices=HDDSTANDBY_CHOICES, 
            default="Always On", 
            verbose_name="HDD Standby"
            )
    disk_advpowermgmt = models.CharField(
            max_length=120, 
            choices=ADVPOWERMGMT_CHOICES, 
            default="Disabled", 
            verbose_name="Advanced Power Management"
            )
    disk_acousticlevel = models.CharField(
            max_length=120, 
            choices=ACOUSTICLVL_CHOICES, 
            default="Disabled", 
            verbose_name="Acoustic Level"
            )
    disk_togglesmart = models.BooleanField(
            default=True,
            verbose_name="Enable S.M.A.R.T.",
            )
    disk_smartoptions = models.CharField(
            max_length=120, 
            verbose_name="S.M.A.R.T. extra options", 
            blank=True
            )
    disk_group = models.ForeignKey(
            DiskGroup,
            verbose_name="Group Membership",
            help_text="The disk group containing this disk"
            )
    class Meta:
        verbose_name = "Disk"
    def __unicode__(self):
        return self.disk_disks + ' (' + self.disk_description + ')'

class MountPoint(Model):
    mp_volume = models.ForeignKey(Volume)
    mp_path = models.CharField(
            unique=True,
            max_length=120,
            verbose_name="Mount Point",
            help_text="Path to mount point",
            )
    mp_options = models.CharField(
            max_length=120,
            verbose_name="Mount options",
            help_text="Enter Mount Point options here",
            null=True,
            )
    mp_ischild = models.BooleanField(
            default=False,
            )
    def __unicode__(self):
        return self.mp_path
    def _get__vfs(self):
        if not hasattr(self, '__vfs'):
            self.__vfs = statvfs(self.mp_path)
        return self.__vfs
    def _get_total_si(self):
        try:
            totalbytes = self._vfs.f_blocks*self._vfs.f_frsize
            return u"%s" % (humanize_number_si(totalbytes))
        except:
            return u"Error getting total space"
    def _get_avail_si(self):
        try:
            availbytes = self._vfs.f_bavail*self._vfs.f_frsize
            return u"%s" % (humanize_number_si(availbytes))
        except:
            return u"Error getting available space"
    def _get_used_si(self):
        try:
            usedbytes = (self._vfs.f_blocks-self._vfs.f_bfree)*self._vfs.f_frsize
            return u"%s" % (humanize_number_si(usedbytes))
        except:
            return u"Error getting used space"
    def _get_used_pct(self):
        try:
            availpct = 100*(self._vfs.f_blocks-self._vfs.f_bavail)/self._vfs.f_blocks
            return u"%d%%" % (availpct)
        except:
            return u"Error"
    _vfs = property(_get__vfs)
    total_si = property(_get_total_si)
    avail_si = property(_get_avail_si)
    used_pct = property(_get_used_pct)
    used_si = property(_get_used_si)

