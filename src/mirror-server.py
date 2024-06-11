from opcua import ua, Server, Client
import time


def read_node_structure(node):
    """
    Recursively read the node structure and values if readable.
    """
    node_structure = {
        'display_name': node.get_display_name().Text,
        'node_class': node.get_node_class(),
        'children': []
    }

    if node_structure['node_class'] in (ua.NodeClass.Variable, ua.NodeClass.Object):
        try:
            node_structure['value'] = node.get_value()
        except:
            node_structure['value'] = None

    for child in node.get_children():
        child_structure = read_node_structure(child)
        node_structure['children'].append(child_structure)

    return node_structure


def create_node_structure(server, parent_node, node_structure):
    """
    Recursively create the node structure in the server.
    """
    if node_structure['node_class'] == ua.NodeClass.Variable:
        new_node = parent_node.add_variable(server.idx, node_structure['display_name'], node_structure.get('value', None))
        new_node.set_writable()  # Make the variable writable
    elif node_structure['node_class'] == ua.NodeClass.Object:
        new_node = parent_node.add_object(server.idx, node_structure['display_name'])
    else:
        return

    for child_structure in node_structure['children']:
        create_node_structure(server, new_node, child_structure)


if __name__ == "__main__":
    # Create a new OPC UA server
    server = Server()
    server.set_endpoint("opc.tcp://localhost:4841/freeopcua/server/")
    server.set_server_name("OPC UA Mirror Server")

    # Setup server namespace
    uri = "http://examples.freeopcua.github.io"
    server.idx = server.register_namespace(uri)

    try:
        # Start the server
        server.start()
        print("Server started")

        # Read the structure from the source server
        client = Client("opc.tcp://localhost:4840/freeopcua/server/")
        try:
            client.connect()
            root = client.get_root_node()
            objects = client.get_objects_node()
            structure = read_node_structure(objects.get_children()[1])
        finally:
            client.disconnect()

        # Create the structure in the new server
        objects_node = server.get_objects_node()
        create_node_structure(server, objects_node, structure)

        print("Structure created in the new server")

        # Keep the server running
        while True:
            time.sleep(1)

    finally:
        # Stop the server
        server.stop()
        print("Server stopped")
