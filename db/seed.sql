-- Datos de ejemplo (borrar o reemplazar por los reales del negocio)
INSERT INTO categoria(nombre) VALUES ('Carnes'),('Insumos'),('Acompañantes'),('Bebidas'),('Empaques'),('Combustible');

INSERT INTO proveedor(nombre, telefono) VALUES
 ('Avícola El Granjero','555-0101'),('Distribuidora Don Pepe','555-0102'),('Carbones del Norte','555-0103');

INSERT INTO producto(nombre,categoria_id,proveedor_id,unidad,stock_minimo,costo_unitario,precio_venta,perecedero) VALUES
 ('Pollo crudo entero',1,1,'unidad',20,3.50,NULL,1),
 ('Pollo asado entero',1,1,'unidad',0,0,9.00,1),
 ('Papas',3,2,'kg',15,0.80,NULL,1),
 ('Salsa de ají',2,2,'litro',3,4.00,NULL,1),
 ('Sal y especias',2,2,'kg',2,2.50,NULL,0),
 ('Carbón',6,3,'saco',5,6.00,NULL,0),
 ('Gaseosa 1.5L',4,2,'unidad',12,1.20,2.50,0),
 ('Bolsas para pollo',5,2,'paquete',4,3.00,NULL,0);

INSERT INTO movimiento(producto_id,tipo,cantidad,costo_unitario,nota) VALUES
 (1,'COMPRA',40,3.50,'Pedido inicial'),(3,'COMPRA',30,0.80,'Pedido inicial'),
 (4,'COMPRA',6,4.00,NULL),(5,'COMPRA',5,2.50,NULL),(6,'COMPRA',10,6.00,NULL),
 (7,'COMPRA',24,1.20,NULL),(8,'COMPRA',10,3.00,NULL),
 (1,'CONSUMO',-25,NULL,'Pollos puestos al horno'),
 (3,'CONSUMO',-18,NULL,NULL),
 (6,'CONSUMO',-6,NULL,NULL),
 (7,'VENTA',-14,NULL,NULL),
 (1,'MERMA',-1,NULL,'Se cayó al piso');
