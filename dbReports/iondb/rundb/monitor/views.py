# Copyright (C) 2012 Ion Torrent Systems, Inc. All Rights Reserved
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response, render
from django.template.context import RequestContext
from django.core.paginator import Paginator, InvalidPage
from iondb.rundb.api import MonitorResultResource
from iondb.rundb.models import GlobalConfig
from iondb.rundb import models

import datetime
import json
import logging
import requests
logger = logging.getLogger(__name__)

@login_required
def monitor(request):
    """This is a the main entry point to the Monitor tab."""
    pageSize = GlobalConfig.objects.all()[0].records_to_display
    resource = MonitorResultResource()
    objects = resource.get_object_list(request)
    paginator = resource._meta.paginator_class(
        request.GET,
        objects,
        resource_uri=resource.get_resource_uri(), 
        limit=pageSize, 
        max_limit=resource._meta.max_limit, 
        collection_name=resource._meta.collection_name
    )
    to_be_serialized = paginator.page()
    to_be_serialized['objects'] = [
        resource.full_dehydrate(resource.build_bundle(obj=obj, request=request)) 
        for obj in to_be_serialized['objects']
    ]
    serialized_exps = resource.serialize(None, to_be_serialized, 'application/json')

    context = {
        'initial_runs': serialized_exps,
        'pageSize' : pageSize
    }
    return render_to_response("rundb/monitor/monitor.html", context,
                              context_instance=RequestContext(request))

def instruments(request):
    queryset = models.MonitorData.objects.all()
    # Make a new model if none exist.
    if len(queryset) == 0:
        m1 = models.MonitorData()
        m1.testDat = json.loads('{"test1":{"test2":"inner"},"test2.5":{"test3":"alsoinner"},"test4":"outer"}')
        m1.name = "Debug"
        m1.save()
        queryset = models.MonitorData.objects.all()
    # DEBUG: use this to just keep one treeview model, so it's clean.
    '''else:
        m1 = queryset[0]
        m1.testDat = json.loads('{"Example1":{"Example2":{"Example3":"n","Example4":"n"},"Example5":"n"},"Example6":"n"}')
        m1.name = "Debug"
        m1.save()
        queryset = models.MonitorData.objects.all()'''
    # Clean excess models.
    '''for i in range(2,20):
        try:
            m = models.MonitorData.objects.get(id=i)
            m.delete()
        except:
            pass'''
    # Prepare Monitor Data sets for being passed to the web page.
    queryset = models.MonitorData.objects.all()
    monitors = []
    for mon in queryset:
        #monitors += json.dumps(mon.testDat)
        monitors.append(mon)
    # Prepare Rig data for being passed to the web page.
    queryset = models.Rig.objects.all()
    rigs = []
    for rig in queryset:
        rigs.append(rig)
    context = { 'extra_data' : monitors, 'rigs' : rigs }
    return render_to_response("rundb/monitor/instruments.html", context, context_instance=RequestContext(request))

def getSoftware(request):
    req = requests.get('http://updates.ite/BB/updates/SoftwareVersionList.txt')
    sofText = req.text
    return HttpResponse(sofText)


def get_int(querydict, key, default=0):
    value = default
    try:
        if key in querydict:
            value = int(querydict.get(key))
    except ValueError:
        pass
    return value


def chef(request):
    querydict = request.GET
    days = get_int(querydict, "days", 2)
    size = get_int(querydict, "size", 10)
    page = get_int(querydict, "page", 1)

    days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
    query = models.PlannedExperiment.objects.exclude(chefLastUpdate=None).filter(chefLastUpdate__gte=days_ago).order_by('chefLastUpdate')
    chef_pager = Paginator(query, size, 0)
    try:
        chef_page = chef_pager.page(page)
    except InvalidPage:
        chef_page = chef_pager.page(1)

    context = {
        "plans": chef_page
    }
    return render(request, "rundb/monitor/chef.html", context)
