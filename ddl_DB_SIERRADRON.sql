-- DDL generado automáticamente desde DB_SIERRADRON
-- Fecha: 2026-03-30 11:04:19
-- Servidor origen: CJCSG-SQLDEV01
-- Generado por: generate_ddl.py
--
-- Para recrear la base de datos en otro servidor:
--   1. Crear la base de datos destino
--   2. Ejecutar este script en orden
-- ============================================================

USE [DB_SIERRADRON];
GO

-- ────────────────────────────────────────────────────
-- Tabla: dbo.Dron_Heartbeats
-- ────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Dron_Heartbeats]', 'U') IS NOT NULL
    DROP TABLE [dbo].[Dron_Heartbeats];
GO

CREATE TABLE [dbo].[Dron_Heartbeats] (
    [HeartbeatTime] DATETIME2(7) NULL,
    [ID] INT IDENTITY(1,1) NOT NULL,
    [Source] VARCHAR(255) NULL,
    CONSTRAINT [PK__Dron_Hea__3214EC27A69D289F] PRIMARY KEY ([ID])
);
GO

-- ────────────────────────────────────────────────────
-- Tabla: dbo.Dron_Stop_Button
-- ────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Dron_Stop_Button]', 'U') IS NOT NULL
    DROP TABLE [dbo].[Dron_Stop_Button];
GO

CREATE TABLE [dbo].[Dron_Stop_Button] (
    [ID] INT IDENTITY(1,1) NOT NULL,
    [USUARIO] NVARCHAR(255) NULL,
    [Fecha] DATETIME2(7) NOT NULL,
    CONSTRAINT [PK__Dron_Sto__3214EC27C4034BD6] PRIMARY KEY ([ID])
);
GO

-- ────────────────────────────────────────────────────
-- Tabla: dbo.Inventario_Vuelos
-- ────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Inventario_Vuelos]', 'U') IS NOT NULL
    DROP TABLE [dbo].[Inventario_Vuelos];
GO

CREATE TABLE [dbo].[Inventario_Vuelos] (
    [ID] INT IDENTITY(1,1) NOT NULL,
    [Nombre_Archivo] NVARCHAR(255) NULL,
    [Fecha_Vuelo] DATETIME NULL,
    [N_elementos] INT NULL,
    [Tiempo_Vuelo] INT NULL,
    [Estado_Inventario] NVARCHAR(10) NULL,
    CONSTRAINT [PK__Inventar__3214EC27360D86BF] PRIMARY KEY ([ID])
);
GO

-- ────────────────────────────────────────────────────
-- Tabla: dbo.Inventarios_JDE
-- ────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Inventarios_JDE]', 'U') IS NOT NULL
    DROP TABLE [dbo].[Inventarios_JDE];
GO

CREATE TABLE [dbo].[Inventarios_JDE] (
    [ID] INT IDENTITY(1,1) NOT NULL,
    [ID_Vuelo] INT NULL,
    [Fecha_Inventario] DATETIME NULL,
    [Elementos_OK] INT NULL,
    [Elementos_Faltantes] INT NULL,
    [Elementos_Sobrantes] INT NULL,
    [Porcentaje_Lectura] FLOAT(53) NULL,
    [NumeroConteo] INT NULL,
    [Sucursal] NVARCHAR(255) NULL,
    [Ubicacion] NVARCHAR(255) NULL,
    [TransactionId] NVARCHAR(255) NULL,
    [Imagen_Vuelo] VARCHAR(255) NULL,
    [Video_Vuelo] VARCHAR(255) NULL,
    CONSTRAINT [PK__Inventar__3214EC27289DCF8B] PRIMARY KEY ([ID]),
    CONSTRAINT [FK__Inventari__ID_Vu__276EDEB3] FOREIGN KEY ([ID_Vuelo]) REFERENCES [Inventario_Vuelos]([ID])
);
GO

-- ────────────────────────────────────────────────────
-- Tabla: dbo.Elementos_JDE
-- ────────────────────────────────────────────────────
IF OBJECT_ID('[dbo].[Elementos_JDE]', 'U') IS NOT NULL
    DROP TABLE [dbo].[Elementos_JDE];
GO

CREATE TABLE [dbo].[Elementos_JDE] (
    [ID] INT IDENTITY(1,1) NOT NULL,
    [EPC] NVARCHAR(255) NULL,
    [Resultado] NVARCHAR(10) NULL,
    [ID_Inventario] INT NULL,
    [Ubicacion] NVARCHAR(255) NULL,
    [CodigoArticulo] NVARCHAR(255) NULL,
    [Fecha_lectura] DATETIME NULL,
    CONSTRAINT [PK__Elemento__3214EC272DCBDEB7] PRIMARY KEY ([ID]),
    CONSTRAINT [FK__Elementos__ID_In__2C3393D0] FOREIGN KEY ([ID_Inventario]) REFERENCES [Inventarios_JDE]([ID])
);
GO

