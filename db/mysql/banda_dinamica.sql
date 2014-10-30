/*
 * Funções auxiliares para calcular banda do usuário dinamicamente
 * no freeradius usando o banco de dados MySQL.
 *
 * As funções devem ser utilizadas com o recurso xlat do freeradius.
 *
 */

DROP FUNCTION IF EXISTS consumo_por_login;
DROP FUNCTION IF EXISTS pega_taxa;
DROP FUNCTION IF EXISTS pega_recv;
DROP FUNCTION IF EXISTS pega_recv_giga;
DROP FUNCTION IF EXISTS pega_xmit;
DROP FUNCTION IF EXISTS pega_xmit_giga;

DELIMITER $$ ;

/*
 * Dado um determinado login, retorna o total em bytes de consumo (download)
 * do usuário.
 * 
 * O total é calculado a partir dos últimos 30 dias de uso.
 */
CREATE FUNCTION consumo_por_login(`ologin` VARCHAR(250))
    RETURNS BIGINT
BEGIN
    DECLARE consumo BIGINT;
    SELECT SUM(acctoutputoctets)
    FROM radacct 
    WHERE 
        (username=ologin) and 
        (acctstoptime>=DATE_SUB(CURDATE(), INTERVAL 30 DAY)) 
    INTO @consumo;
    RETURN COALESCE(@consumo, 0);
END$$

/*
 * Quando o usuário atingir 50% da sua cota, fixar a velocidade dele em 
 * 40% da banda contratada. 
 * Quando atingir 100% da sua cota, o tratamento será o que já está sendo 
 * feito hoje.
 */
CREATE FUNCTION `pega_taxa`(`rate1` VARCHAR(250), `rate2` VARCHAR(250), `login` VARCHAR(250), `quota` BIGINT) 
    RETURNS varchar(250) CHARSET latin1
    READS SQL DATA
BEGIN
    DECLARE consumo BIGINT;
    DECLARE _rate_up   BIGINT;
    DECLARE _rate_down BIGINT;
    DECLARE _pos INT;
    DECLARE nova_taxa  VARCHAR(250);
    SELECT consumo_por_login(login) INTO @consumo;
    IF @consumo >= quota THEN -- usuario atinge 100% da cota, retornar rate2
        RETURN rate2;  
    ELSEIF @consumo >= quota/2 THEN  -- usuario atinge 50% da cota, fixar a taxa em 40% da contratada
        SET rate1 = CONCAT(REPLACE(rate1, 'k', ''), ' ');    -- adicionei o espaco no final para facilitar a extracão de taxas com burst.
        SET rate1 = SUBSTRING(rate1, 1, LOCATE(' ', rate1)); -- elimina os atributos do burst
        SET _pos = LOCATE('/', rate1);
        SET _rate_up   = CAST(SUBSTRING(rate1, 1, _pos-1) AS UNSIGNED)*0.4;
        SET _rate_down = CAST(SUBSTRING(rate1, _pos+1) AS UNSIGNED)*0.4;
        SET nova_taxa  = CONCAT(CAST(_rate_up AS CHAR(32)), 'k/', CAST(_rate_down AS CHAR(32)), 'k');
        RETURN nova_taxa; 
    ELSE
        RETURN rate1; -- taxa normal antes de atingir a quota
    END IF;
END$$

-- ==================================================================
-- ==================================================================
-- ==================================================================

CREATE FUNCTION `pega_recv`(`login` VARCHAR(250), `quota` BIGINT) 
    RETURNS varchar(250) CHARSET latin1
    READS SQL DATA
BEGIN
    DECLARE consumo BIGINT;
    SELECT consumo_por_login(login) INTO @consumo;
    IF @consumo <= quota THEN
        RETURN (quota - @consumo) & 4294967295;
    ELSE
        RETURN '0';
    END IF;
END$$

CREATE FUNCTION `pega_recv_giga`(`login` VARCHAR(250), `quota` BIGINT) 
    RETURNS varchar(250) CHARSET latin1
    READS SQL DATA
BEGIN
    DECLARE consumo BIGINT;
    SELECT consumo_por_login(login) INTO @consumo;
    IF @consumo <= quota THEN
        RETURN (quota - @consumo) >> 32;
    ELSE
        RETURN '0';
    END IF;
END$$

-- ==================================================================
-- ==================================================================
-- ==================================================================

CREATE FUNCTION `pega_xmit`(`login` VARCHAR(250), `quota` BIGINT) 
    RETURNS varchar(250) CHARSET latin1
    READS SQL DATA
BEGIN
    DECLARE consumo BIGINT;
    SELECT consumo_por_login(login) INTO @consumo;
    IF @consumo <= quota THEN
        RETURN (quota - @consumo) & 4294967295;
    ELSE
        RETURN '0';
    END IF;
END$$

CREATE FUNCTION `pega_xmit_giga`(`login` VARCHAR(250), `quota` BIGINT) 
    RETURNS varchar(250) CHARSET latin1
    READS SQL DATA
BEGIN
    DECLARE consumo BIGINT;
    SELECT consumo_por_login(login) INTO @consumo;
    IF @consumo <= quota THEN
        RETURN (quota - @consumo) >> 32;
    ELSE
        RETURN '0';
    END IF;
END$$

DELIMITER ;

