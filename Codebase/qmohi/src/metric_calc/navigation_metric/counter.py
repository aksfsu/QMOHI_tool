import copy
import re
import qmohi.src.metric_calc.navigation_metric.constants as constants
from qmohi.src.metric_calc.navigation_metric.tree_structure import Node, set_up_selenium_driver


def get_count(nodes, call_level, target_urls):

    child_nodes = []
    cur_level = call_level + 1
    print("      - Searching web pages with minimum number of clicks =",cur_level)
    if cur_level <= constants.LEVEL_THRESHOLD:
        status = 0

        for cur_node in nodes:
            for page in cur_node.child_pages:
                parent_node_trace = copy.copy(cur_node.trace)
                obj = Node(url=page, level=cur_level, target_urls=target_urls, trace=parent_node_trace)
                child_nodes.append(obj)

                # If URL match found with target URLs
                if obj.hit != -1:
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
    cleaned_urls = []
    for check in url_filter:
        for url in target_urls:
            if url.find(check) == -1:
                # Doesn't contain a given substring of pdf/doc
                cleaned_urls.append(url)

    return cleaned_urls


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
        print("      - Searching web pages with minimum number of clicks = 0")
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
