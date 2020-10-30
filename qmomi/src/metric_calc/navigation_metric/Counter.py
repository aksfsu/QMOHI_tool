import copy
import re
import qmomi.src.metric_calc.navigation_metric.constants as constants
from qmomi.src.metric_calc.navigation_metric.TreeStructure import Node, set_up_selenium_driver


def get_count(nodes, call_level, target_urls):

    child_nodes = []
    cur_level = call_level + 1
    print(f"Creating nodes at level {cur_level}")
    if cur_level <= constants.LEVEL_THRESHOLD:
        status = 0

        for cur_node in nodes:
            for page in cur_node.child_pages:
                parent_node_trace = copy.copy(cur_node.trace)
                obj = Node(url=page, level=cur_level, target_urls=target_urls, trace=parent_node_trace)
                child_nodes.append(obj)
                if obj.hit != -1:
                    # print(f"------->>>> found HIT here {obj.url} ------->>>>")
                    print(f"------>>>> Trace : {obj.trace}")
                    constants.trace = obj.trace
                    status = 1
                    break
            if status == 1:
                break

        if all([child.hit == -1 for child in child_nodes]):
            cur_level = get_count(child_nodes, cur_level, target_urls)

        return cur_level
    else:
        return constants.INVALID_CLICKS, []


def clean_target_urls(target_urls):
    if isinstance(target_urls, str):
        target_urls = re.findall(r"'(.*?)'", target_urls)

    # Check for pdf, doc and remove them
    url_filter = ['.pdf', '.doc', '.docx']
    for check in url_filter:
        for url in target_urls:
            if url.find(check) != -1:
                print("Contains given substring ")
                target_urls.remove(url)

    return target_urls


def get_min_click_count(no_of_links, links, shc_url, driver_path):

    min_clicks = -1
    # If no matching URL found!
    if no_of_links == 0:
        pass
    else:
        set_up_selenium_driver(driver_path)
        target_urls = clean_target_urls(links)
        constants.visited_urls = []
        constants.visited_urls.append(shc_url)
        root_node = Node(url = shc_url,
                         level = 0,
                         target_urls = target_urls,
                         trace = [])

        if root_node.hit != -1:
            min_clicks = root_node.hit
            constants.trace = [shc_url]
        else:
            clicks = get_count(nodes = [root_node],
                               call_level = 0,
                               target_urls = target_urls)

            if clicks == constants.INVALID_CLICKS:
                constants.trace = []
                pass
            else:
                min_clicks = clicks

    return min_clicks, constants.trace
