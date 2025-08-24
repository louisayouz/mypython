
CREATE DATABASE py_mydev
    WITH
    OWNER = louisayouz
    ENCODING = 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

CREATE SEQUENCE portfolios_id_seq;
 CREATE TABLE IF NOT EXISTS portfolios (
    id integer NOT NULL DEFAULT nextval('portfolios_id_seq'::regclass),
    user_id integer NOT NULL,
    portfolio_name character varying(255),
	created_at timestamp without time zone,
    updated_at timestamp without time zone,
	CONSTRAINT portfolios_pkey PRIMARY KEY (id),
	CONSTRAINT portfolios_name_key UNIQUE (portfolio_name)

);

CREATE SEQUENCE portfolios_id_seq;
CREATE TABLE portfolio_quotes (
    id integer NOT NULL DEFAULT nextval('portfolio_quotes_id_seq'::regclass),
    portfolio_id integer NOT NULL,
    quote_name character varying(32),
	buy_price numeric(8,3),
	buy_count integer,

	created_at timestamp without time zone,
    updated_at timestamp without time zone,
	CONSTRAINT portfolio_quotes_pkey PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS index_portfolio_quotes_on_portfolio_id_quote_name
ON public.portfolio_quotes USING btree
(portfolio_id, quote_name,  from_year, from_month)
WHERE from_year IS NOT NULL AND from_month IS NOT NULL;

CREATE SEQUENCE quote_dividents_id_seq;
CREATE TABLE quote_dividents (
    id integer NOT NULL DEFAULT nextval('quote_dividents_id_seq'::regclass),
    quote_name character varying(32),
	  div_price numeric(8,3),
	  pay_year integer,
	  pay_month integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
	CONSTRAINT quote_dividents_key UNIQUE (quote_name, pay_year, pay_month)
);

ALTER TABLE portfolio_quotes
	ADD COLUMN from_year INTEGER CHECK (from_year BETWEEN 2010 AND 2100),
	ADD COLUMN from_month SMALLINT CHECK (from_month BETWEEN 1 AND 12),
	ADD COLUMN to_year INTEGER CHECK (to_year BETWEEN 2010 AND 2100),
	ADD COLUMN to_month  SMALLINT CHECK (to_month BETWEEN 1 AND 12);

CREATE SEQUENCE quotes_id_seq;
CREATE TABLE quotes (
    id integer NOT NULL DEFAULT nextval('quotes_id_seq'::regclass),
    quote_name character varying(32),
	created_at timestamp without time zone,
    updated_at timestamp without time zone,
	CONSTRAINT quote_names UNIQUE (quote_name)
);

CREATE SEQUENCE portfolio_quotes_id_seq;
CREATE TABLE IF NOT EXISTS public.portfolio_quotes
(
    id integer NOT NULL DEFAULT nextval('portfolio_quotes_id_seq'::regclass),
    portfolio_id integer NOT NULL,
    quote_name character varying(32) COLLATE pg_catalog."default",
    buy_price numeric(8,3),
    buy_count integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    from_year integer,
    from_month smallint,
    to_year integer,
    to_month smallint,
    current_quotes_count integer,
    CONSTRAINT portfolio_quotes_pkey PRIMARY KEY (id),
    CONSTRAINT portfolio_quotes_from_year_check CHECK (from_year >= 2010 AND from_year <= 2100),
    CONSTRAINT portfolio_quotes_from_month_check CHECK (from_month >= 1 AND from_month <= 12),
    CONSTRAINT portfolio_quotes_to_year_check CHECK (to_year >= 2010 AND to_year <= 2100),
    CONSTRAINT portfolio_quotes_to_month_check CHECK (to_month >= 1 AND to_month <= 12)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.portfolio_quotes
    OWNER to louisayouz;
-- Index: index_portfolio_id

-- DROP INDEX IF EXISTS public.index_portfolio_id;

CREATE INDEX IF NOT EXISTS index_portfolio_id
    ON public.portfolio_quotes USING btree
    (portfolio_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: index_portfolio_quotes_on_portfolio_id_quote_name

-- DROP INDEX IF EXISTS public.index_portfolio_quotes_on_portfolio_id_quote_name;

CREATE UNIQUE INDEX IF NOT EXISTS index_portfolio_quotes_on_portfolio_id_quote_name
    ON public.portfolio_quotes USING btree
    (portfolio_id ASC NULLS LAST, quote_name COLLATE pg_catalog."default" ASC NULLS LAST, from_year ASC NULLS LAST, from_month ASC NULLS LAST)
    TABLESPACE pg_default
    WHERE from_year IS NOT NULL AND from_month IS NOT NULL;


CREATE SEQUENCE users_id_seq;
CREATE TABLE IF NOT EXISTS public.users
(
    id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    username text COLLATE pg_catalog."default" NOT NULL,
    password text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_username_key UNIQUE (username)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.users OWNER to louisayouz;
ALTER TABLE users ADD COLUMN password_hash BYTEA;


CREATE TABLE IF NOT EXISTS public.quotes_price
(
    id integer NOT NULL DEFAULT nextval('quote_price_id_seq'::regclass),
    quote_name character varying(32) COLLATE pg_catalog."default" NOT NULL,
    close_price numeric(8,3) NOT NULL ,
    last_date_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
)

CREATE UNIQUE INDEX IF NOT EXISTS quotes_price_last
    ON public.quotes_price USING btree
    (quote_name COLLATE pg_catalog."default" ASC NULLS LAST,
     last_date_at DESC NULLS LAST)
    TABLESPACE pg_default;

