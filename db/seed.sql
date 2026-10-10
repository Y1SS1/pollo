-- Datos de ejemplo (reemplazar por los reales del negocio)
INSERT INTO categoria(nombre) VALUES ('Carnes'),('Insumos'),('Acompañantes'),('Bebidas'),('Empaques'),('Combustible');

INSERT INTO proveedor(nombre, telefono) VALUES
 ('Avícola El Granjero','555-0101'),('Distribuidora Don Pepe','555-0102'),('Carbones del Norte','555-0103');

INSERT INTO producto(nombre,categoria_id,proveedor_id,unidad,stock_minimo,costo_unitario,perecedero) VALUES
 ('Pollo crudo entero',1,1,'unidad',10,3.50,1),
 ('Papas',3,2,'kg',15,0.80,1),
 ('Salsa de ají',2,2,'litro',3,4.00,1),
 ('Sal y especias',2,2,'kg',2,2.50,0),
 ('Carbón',6,3,'saco',5,6.00,0),
 ('Gaseosa 1.5L',4,2,'unidad',12,1.20,0),
 ('Bolsas para pollo',5,2,'unidad',50,0.05,0);

INSERT INTO plato(nombre,precio) VALUES
 ('1/4 de pollo',4.00),('1/4 de pollo con papas fritas',5.50),
 ('1/2 pollo',7.50),('Pollo entero',14.00),('Gaseosa 1.5L',2.50);

-- Recetas (cantidad por 1 unidad vendida)
INSERT INTO receta(plato_id,producto_id,cantidad) VALUES
 (1,1,0.25),(1,4,0.01),(1,7,1),
 (2,1,0.25),(2,4,0.01),(2,7,1),(2,2,0.30),(2,3,0.03),
 (3,1,0.50),(3,4,0.02),(3,7,1),
 (4,1,1.00),(4,4,0.04),(4,7,1),
 (5,6,1);

INSERT INTO movimiento(producto_id,tipo,cantidad,costo_unitario,nota) VALUES
 (1,'COMPRA',40,3.50,'Pedido inicial'),(2,'COMPRA',30,0.80,'Pedido inicial'),
 (3,'COMPRA',6,4.00,NULL),(4,'COMPRA',5,2.50,NULL),(5,'COMPRA',10,6.00,NULL),
 (6,'COMPRA',24,1.20,NULL),(7,'COMPRA',300,0.05,NULL);
