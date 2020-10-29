import copy
import re
import qmomi.src.metric_calc.navigation_metric.constants as constants
from qmomi.src.metric_calc.navigation_metric import Node


def get_count(nodes, call_level, target_urls):

    child_nodes = []
    cur_level = call_level + 1
    print(f"Creating nodes at level {cur_level}")
    if cur_level <= constants.LEVEL_THRESHOLD:
        status = 0

        for cur_node in nodes:
            for page in cur_node.child_pages:
                # cur_node.trace.append(page)
                # print(page)
                parent_node_trace = copy.copy(cur_node.trace)
                obj = Node(url=page, level=cur_level, target_urls=target_urls, trace=parent_node_trace)
                child_nodes.append(obj)
                if obj.hit != -1:
                    # print(f"------->>>> found HIT here {obj.url} ------->>>>")
                    print(f"------>>>> Trace : {obj.trace}")
                    constants.trace = obj.trace
                    # trace = obj.trace
                    # print(f"------->>>> cur level: {cur_level}")
                    status = 1
                    break
            if status ==1:
                break


        if all([child.hit == -1 for child in child_nodes]):
            cur_level = get_count(child_nodes, cur_level, target_urls)
        # print("#############Current level: ", cur_level)

        return cur_level
    else:
        return constants.INVALID_CLICKS, []


def clean_target_urls(target_urls):
    if isinstance(target_urls, str):
        target_urls = re.findall(r"'(.*?)'", target_urls)
    # check for pdf, doc and remove them
    url_filter = ['.pdf', '.doc', '.docx']
    for check in url_filter:
        for url in target_urls:
            if url.find(check) != -1:
                print("Contains given substring ")
                target_urls.remove(url)

    return target_urls


def get_min_click_count(no_of_links, links, shc_url):
    # df = pd.DataFrame(univ, columns=['University name', 'University SHC URL',
    #                                  'Count of keywords matching webpages on SHC',
    #                                  'Keywords matched webpages on SHC', 'min_clicks'])
    min_clicks = -1
    trace = []
    if no_of_links == 0:
        # print(f"{df['University name'].values[0]} : No matching URL found!")
        pass
    else:
        target_urls = clean_target_urls(links)
        constants.visited_urls = []
        # print(f"{df['University name'].values[0]} : matching URL found!")
        constants.visited_urls.append(shc_url)
        root_node = Node(url=shc_url,
                         level=0,
                         target_urls=target_urls,
                         trace= [])


        if root_node.hit != -1:
            min_clicks = root_node.hit
            constants.trace = [shc_url]
        else:
            clicks = get_count(nodes=[root_node],
                               call_level=0,
                               target_urls=target_urls)

            # clicks = navigation[0][0] ### recursive call creating tuples
            # trace = navigation[0][1]
            if clicks == constants.INVALID_CLICKS:
                constants.trace = []
                pass
            else:
                min_clicks = clicks

    return min_clicks, constants.trace


# def get_all_min_click_count(df):
#
#     df = df.assign(min_clicks=-1)
#
#     df_split = np.array_split(df.values, len(df))
#     # print("============")
#
#     # partial_fun = partial(get_min_click_count)
#     with mp.Pool(constants.n_processes) as p:
#         univ = p.map(get_min_click_count, df_split)
#         # univ = p.map(partial_fun, df_split)
#         all_univ = pd.concat(univ)
#         p.close()
#         p.join()
#
#     return all_univ
