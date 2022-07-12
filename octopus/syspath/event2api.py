"""
This file contains the functions that are used to 
build api trace from a syscall event trace.
"""

from collections import defaultdict
from octopus.syspath.api import API
from octopus.syspath.trie import Trie

def event_trace2api_trace(event_trace, api2trace, used_api, graph = None):
    """
    Translate syscall event trace generated by sysdig to possible api call trace.
    """
    
    trie = build_trie(api2trace, used_api)
    apis, traces = [], []
    chunks = [event_trace[x:x+100] for x in range(0, len(event_trace), 100)]
    for chunk in chunks:
        part_apis, part_traces = dfs(trie, chunk)[0]
        apis.extend(list(part_apis))
        traces.extend(list(part_traces))
    api_trace = [(apis, traces)]
    
    # try:
    #     api_trace = dfs(trie, event_trace)
    # except RecursionError as re:
    #     print("RecursionError detected. reconstruct the api trace segmentation by segmentation")
        


    # change list to tuple to make it hashable
    ret = []
    for result in api_trace:
        apis, cor_traces = result
        apis = tuple([tuple(_) for _ in apis])
        cor_traces = tuple([tuple(_) for _ in cor_traces])
        ret.append((apis, cor_traces))
    return ret
    
    # handle compiler optimization, e.g., printf optimized to puts
    """
    api_trace_after_handle_compile_opt = []
    for apis, traces in api_trace:
        new_apis, new_traces = [], []
        for i in range(len(apis)):
            api = apis[i]
            trace = traces[i]
            if api[0] == "putc" or api[0] == "puts":
                api.append("printf")
            if api[0] == "fputc" or api[0] == "fputs":
                api.append("fprintf")
            new_apis.append(api)
            new_traces.append(trace)
        api_trace_after_handle_compile_opt.append((new_apis, new_traces))

    return api_trace_after_handle_compile_opt
    """

    

    # trace2api = build_FSM(api2trace, used_api)
    # trace_keys = list(trace2api.keys())
    # trace_keys = sorted(trace_keys, key=lambda e: len(e.split("$")), reverse=True)
    # trace key is calculated and sorted once to avoid redundent computation
    # return greedy(event_trace, trace2api, trace_keys, graph)

def build_trie(api2trace, used_api):
    t = Trie()
    t.set_used_api(used_api)
    for api in api2trace:
        traces = api2trace[api]
        for trace in traces:
            trace_list = trace.split("$")[:-1]
            t.insert(trace_list, api)
    return t



def greedy(to_match, trace2api, trace_keys, graph = None):
    """
    greedy algorithm used in event_trace2api_trace
    """
    if not to_match:
        return []
    res = []
    NOT_MATCH = 'n'
    flag = False
    for trace in trace_keys:
        matched_api = trace2api[trace] # matched api is a list containing all possble matched apis
        trace_list = trace2list(trace)
        l = len(trace_list)
        if match(trace_list, to_match[:l]):
            for api in matched_api:
                tmp_res = []
                candidate_api = []
                if api in graph.specFunc:
                    # try to use additional info to infer the syscall position
                    candidate_pos = graph.infer_position(api, to_match[:l])
                    if not candidate_pos:
                        candidate_api.append(API(api))
                    else:
                        for pos in candidate_pos:
                            api_obj = API(api)
                            api_obj.set_position(pos)
                            candidate_api.append(api_obj)
                else:
                    candidate_api.append(API(api))
                sub_res = greedy(to_match[l:], trace2api, trace_keys, graph)
                if sub_res == NOT_MATCH:
                    continue
                else:
                    flag = True
                    if len(sub_res) == 0:
                        for api_obj in candidate_api:
                            tmp_res.append([api_obj])
                    for s in sub_res:
                        for api_obj in candidate_api:
                            tmp_res.append([api_obj] + s)
                for r in tmp_res:
                    res.append(r)
    if not flag:
        return NOT_MATCH
    return res

def match(trace_list, event_list):
    for i in range(len(trace_list)):
        if trace_list[i] != event_list[i].event_type:
            return False
    return True


def build_FSM(api2trace, used_api):
    """
    Currently, it's actually a reverse index of api2trace
    Is there any algorithm to build FSM automatically?
    """
    trace2api = defaultdict(list)
    for api in api2trace:
        if api in used_api:
            for trace in api2trace[api]:
                if api not in trace2api[trace]:
                    trace2api[trace].append(api)
    return trace2api


def trace2list(trace_key):
    return trace_key.split("$")[:-1]


def dfs(trie, event_trace):
    res = []
    matched_apis = trie.match_from_head(event_trace)
    for matched_api, matched_num in matched_apis:
        left_event_trace = event_trace[matched_num:]
        if left_event_trace == []:
            res.append(([matched_api], [event_trace[:matched_num]]))
        else:
            left_res = dfs(trie, left_event_trace)
            for item, item_corespond_event in left_res:
                if item == [[]]:
                    res.append(([matched_api], [event_trace[:matched_num]]))
                    continue
                res.append(([matched_api] + item, [event_trace[:matched_num]] + item_corespond_event))
    return res
    